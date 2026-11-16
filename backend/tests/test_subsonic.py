import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import subsonic
from models import StreamTrack, User, Playlist, PlaylistTrack, MusicTrack, MusicTrackFile, Album
from routers import subsonic as routes
from auth.auth import get_user, is_admin
from db import get_db


class SubsonicTestBase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.data_patch = patch.object(subsonic, "DATA", Path(self.directory.name))
        self.data_patch.start()
        self.connection = subsonic.Connection(
            url="https://music.example.com/base/rest/", username="user", password="密碼")
        subsonic.save_connection(self.connection)

    def tearDown(self):
        self.data_patch.stop()
        self.directory.cleanup()

    def response(self, data=b"audio-data", content_type="audio/mpeg"):
        return httpx.Response(200, content=data, headers={
            "Content-Type": content_type, "Content-Length": str(len(data))},
            request=httpx.Request("GET", "https://music.example.com"))

class SubsonicTests(SubsonicTestBase):
    def test_auth_uses_utf8_salted_token_and_no_password(self):
        params = subsonic.params(self.connection, id="a/b & c")
        self.assertNotIn("p", params)
        self.assertEqual(params["t"], hashlib.md5(("密碼" + params["s"]).encode()).hexdigest())
        self.assertNotEqual(params["s"], subsonic.params(self.connection)["s"])
        self.assertEqual(self.connection.url, "https://music.example.com/base")
        self.assertEqual(subsonic.connection_for(subsonic.song_url(self.connection, "a/b & c"))[1], "a/b & c")

    def test_api_failure_inside_http_200(self):
        response = self.response(b'{"subsonic-response":{"status":"failed","error":{"code":40}}}', "application/json")
        with patch.object(subsonic.httpx, "get", return_value=response):
            with self.assertRaisesRegex(subsonic.SubsonicError, "40"):
                subsonic.call(self.connection, "ping")

    def test_cached_audio_works_after_disconnect_and_restart(self):
        url = subsonic.song_url(self.connection, "song")
        with patch.object(subsonic.httpx, "stream") as stream:
            stream.return_value.__enter__.return_value = self.response()
            path = subsonic.cached_audio(url)
        subsonic.disconnect()
        with patch.object(subsonic.httpx, "stream", side_effect=AssertionError("must not connect")):
            self.assertEqual(subsonic.cached_audio(url).read_bytes(), b"audio-data")
        self.assertEqual(path, subsonic.cache_path(url))

    def test_uncached_audio_after_disconnect_is_recoverable(self):
        url = subsonic.song_url(self.connection, "song")
        subsonic.disconnect()
        with self.assertRaises(subsonic.SubsonicError):
            subsonic.cached_audio(url)
        subsonic.save_connection(self.connection)
        with patch.object(subsonic.httpx, "stream") as stream:
            stream.return_value.__enter__.return_value = self.response()
            self.assertTrue(subsonic.cached_audio(url).exists())

    def test_interrupted_download_never_publishes_partial_file(self):
        class Interrupted(httpx.SyncByteStream):
            def __iter__(self):
                yield b"partial"
                raise httpx.ReadError("disconnected")
        response = httpx.Response(200, stream=Interrupted(), headers={"content-type": "audio/mpeg"},
                                  request=httpx.Request("GET", "https://music.example.com"))
        url = subsonic.song_url(self.connection, "song")
        with patch.object(subsonic.httpx, "stream") as stream:
            stream.return_value.__enter__.return_value = response
            with self.assertRaises(subsonic.SubsonicError):
                subsonic.cached_audio(url)
        self.assertFalse(subsonic.cache_path(url).exists())
        self.assertFalse(subsonic.cache_path(url).with_suffix(".part").exists())

    def test_rejects_error_document_as_audio(self):
        url = subsonic.song_url(self.connection, "song")
        with patch.object(subsonic.httpx, "stream") as stream:
            stream.return_value.__enter__.return_value = self.response(b'{"error":40}', "application/json")
            with self.assertRaises(subsonic.SubsonicError):
                subsonic.cached_audio(url)
        self.assertFalse(subsonic.cache_path(url).exists())

    def test_other_source_cannot_resolve_old_uncached_song(self):
        url = subsonic.song_url(self.connection, "song")
        subsonic.save_connection(self.connection.model_copy(update={"username": "another-user"}))
        with self.assertRaises(subsonic.SubsonicError):
            subsonic.connection_for(url)

    def test_library_paging_and_repeated_page_detection(self):
        def api(connection, method, **params):
            if method == "getAlbumList2":
                return {"albumList2": {"album": [{"id": "a"}] if params["offset"] == 0 else []}}
            return {"album": {"song": [{"id": "s"}]}}
        with patch.object(subsonic, "call", side_effect=api):
            self.assertEqual(subsonic.library(self.connection), [{"id": "s"}])
        with patch.object(subsonic, "call", return_value={"albumList2": {"album": [{"id": "a"}]}}):
            with self.assertRaises(subsonic.SubsonicError):
                subsonic.library(self.connection)


class SubsonicRouteTests(SubsonicTestBase):
    def setUp(self):
        super().setUp()
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(self.engine, tables=[model.__table__ for model in (
            StreamTrack, User, Playlist, PlaylistTrack, MusicTrack, MusicTrackFile, Album)])
        self.app = FastAPI()
        self.app.include_router(routes.subsonic_router)
        from routers.stream import stream_router
        self.app.include_router(stream_router)
        def session():
            with Session(self.engine) as value:
                yield value
        self.app.dependency_overrides[get_db] = session
        self.app.dependency_overrides[get_user] = lambda: User(id=1, username="test", password_hash="unused")
        self.app.dependency_overrides[is_admin] = lambda: object()
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        super().tearDown()

    def test_sync_idempotent_and_failed_sync_preserves_library(self):
        song = {"id": "remote-id", "title": "Song", "artist": "Artist", "duration": 42, "coverArt": "art/a"}
        with patch.object(subsonic, "library", return_value=[song]):
            self.assertEqual(self.client.post("/subsonic/sync").status_code, 200)
            self.assertEqual(self.client.post("/subsonic/sync").status_code, 200)
        tracks = self.client.get("/subsonic/tracks").json()
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["kind"], "stream")
        self.assertFalse(tracks[0]["cached"])
        self.assertIn("art%2Fa", tracks[0]["cover_art"])
        with patch.object(subsonic, "library", side_effect=subsonic.SubsonicError("offline")):
            self.assertEqual(self.client.post("/subsonic/sync").status_code, 502)
        self.assertEqual(self.client.get("/subsonic/tracks").json(), tracks)
        self.assertNotIn("password", self.client.get("/subsonic/connection").json())
        self.assertEqual(self.client.delete("/subsonic/connection").status_code, 200)
        self.assertEqual(self.client.get("/subsonic/tracks").json(), tracks)

    def test_failed_connect_preserves_previous_credentials(self):
        with patch.object(subsonic, "call", side_effect=subsonic.SubsonicError("bad credentials")):
            response = self.client.put("/subsonic/connection", json={
                "url": "https://other.example.com", "username": "wrong", "password": "wrong"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(subsonic.load_connection(), self.connection)

    def test_connection_requires_authentication(self):
        self.app.dependency_overrides.clear()
        self.assertEqual(self.client.get("/subsonic/connection").status_code, 401)
        self.assertEqual(self.client.delete("/subsonic/connection").status_code, 401)

    def test_cached_stream_supports_range_after_disconnect(self):
        with patch.object(subsonic, "library", return_value=[{"id": "song", "title": "Song"}]):
            self.client.post("/subsonic/sync").raise_for_status()
        track = self.client.get("/subsonic/tracks").json()[0]
        with patch.object(subsonic.httpx, "stream") as stream:
            stream.return_value.__enter__.return_value = self.response()
            self.client.post(f"/subsonic/cache/{track['id']}").raise_for_status()
        self.client.delete("/subsonic/connection").raise_for_status()
        with patch.object(subsonic.httpx, "stream", side_effect=AssertionError("must stay offline")):
            response = self.client.get(f"/stream/stream/{track['id']}", headers={"Range": "bytes=2-5"})
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, b"dio-")
        self.assertEqual(response.headers["content-range"], "bytes 2-5/10")
        self.assertTrue(self.client.get("/subsonic/tracks").json()[0]["cached"])

    def test_uncached_stream_returns_503_and_reconnect_recovers(self):
        with patch.object(subsonic, "library", return_value=[{"id": "song"}]):
            self.client.post("/subsonic/sync").raise_for_status()
        track = self.client.get("/subsonic/tracks").json()[0]
        self.client.delete("/subsonic/connection").raise_for_status()
        self.assertEqual(self.client.get(f"/stream/stream/{track['id']}").status_code, 503)
        subsonic.save_connection(self.connection)
        with patch.object(subsonic.httpx, "stream") as stream:
            stream.return_value.__enter__.return_value = self.response()
            response = self.client.get(f"/stream/stream/{track['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"audio-data")

    def test_playlist_track_survives_disconnect_and_resync(self):
        from routers.playlist import playlist_router
        self.app.include_router(playlist_router)
        with patch.object(subsonic, "library", return_value=[{"id": "song"}]):
            self.client.post("/subsonic/sync").raise_for_status()
        track = self.client.get("/subsonic/tracks").json()[0]
        playlist = self.client.post("/playlist/playlist", json={"name": "Subsonic"}).json()
        response = self.client.post(f"/playlist/playlist/{playlist['id']}", json={"stream_id": track["id"]})
        self.assertEqual(response.status_code, 200)
        self.client.delete("/subsonic/connection").raise_for_status()
        saved = self.client.get(f"/playlist/playlist/{playlist['id']}").json()["tracks"]
        self.assertEqual(saved[0]["streamtrack"]["id"], track["id"])
        subsonic.save_connection(self.connection)
        with patch.object(subsonic, "library", return_value=[{"id": "song", "title": "Updated"}]):
            self.client.post("/subsonic/sync").raise_for_status()
        saved = self.client.get(f"/playlist/playlist/{playlist['id']}").json()["tracks"]
        self.assertEqual(saved[0]["streamtrack"]["id"], track["id"])
        self.assertEqual(saved[0]["streamtrack"]["title"], "Updated")


if __name__ == "__main__":
    unittest.main()
