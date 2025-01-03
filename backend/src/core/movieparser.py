import requests
from typing import Optional
from pydantic import BaseModel


class CastInfo(BaseModel):
    name: str
    character: str
    profile_path: Optional[str] = None
    profile_url: Optional[str] = None


class MovieInfo(BaseModel):
    title: str
    original_title: str
    release_date: str
    overview: str
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    vote_average: float
    genres: list[str]
    backdrop_url: Optional[str] = None
    poster_url: Optional[str] = None
    cast: list[CastInfo] = []


class TMDBApi:
    BASE_URL = "https://api.themoviedb.org/3"
    BG_URL = "https://media.themoviedb.org/t/p/w1920_and_h800_multi_faces"
    POSTER_URL = "https://image.tmdb.org/t/p/w600_and_h900_bestv2"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def search_movie(self, query: str, language: str = "zh-TW") -> Optional[MovieInfo]:
        try:
            r = requests.get(
                f"{self.BASE_URL}/search/movie",
                headers=self.headers,
                params={"query": query, "language": language},
            )
            r.raise_for_status()
            data = r.json()
            if len(data["results"]) == 0:
                return None

            movie_id = data["results"][0]["id"]
            return self.get_movie_details(movie_id, language)

        except requests.RequestException as e:
            print(f"搜尋錯誤: {str(e)}")
            return None

    def get_movie_details(
        self, movie_id: int, language: str = "zh-TW"
    ) -> Optional[MovieInfo]:
        try:
            r = requests.get(
                f"{self.BASE_URL}/movie/{movie_id}",
                headers=self.headers,
                params={"language": language},
            )
            r.raise_for_status()
            data = r.json()
            credits_response = requests.get(
                f"{self.BASE_URL}/movie/{movie_id}/credits", headers=self.headers
            )
            credits_response.raise_for_status()
            credits_data = credits_response.json()

            cast = []
            for actor in credits_data.get("cast", [])[:5]:
                profile_path = actor.get("profile_path")
                cast.append(
                    CastInfo(
                        name=actor["name"],
                        character=actor["character"],
                        profile_path=profile_path,
                        profile_url=f"https://image.tmdb.org/t/p/w185{profile_path}"
                        if profile_path
                        else None,
                    )
                )
            return MovieInfo(
                title=data["title"],
                original_title=data["original_title"],
                release_date=data["release_date"],
                overview=data["overview"],
                poster_path=data.get("poster_path"),
                backdrop_path=data.get("backdrop_path"),
                vote_average=data["vote_average"],
                genres=[genre["name"] for genre in data["genres"]],
                backdrop_url=f"{self.BG_URL}{data['backdrop_path']}",
                poster_url=f"{self.POSTER_URL}{data['poster_path']}",
                cast=cast,
            )

        except requests.RequestException as e:
            print(f"獲取詳細資訊錯誤: {str(e)}")
            return None


if __name__ == "__main__":
    API_KEY = ""
    tmdb = TMDBApi(API_KEY)
    movie = tmdb.search_movie(
        "ソードアート·オンライン -プログレッシブ- 星なき夜のアリア"
    )
    if movie:
        print(f"標題: {movie.title}")
        print(f"原標題: {movie.original_title}")
        print(f"發行日期: {movie.release_date}")
        print(f"概要: {movie.overview}")
        print(f"類型: {', '.join(movie.genres)}")
        print(f"評分: {movie.vote_average}")
        print(f"背景圖: {movie.backdrop_url}")
        print(f"海報: {movie.poster_url}")
        print("\n主要演員:")
        for actor in movie.cast:
            print(f"{actor.name} 飾演 {actor.character}")
            if actor.profile_url:
                print(f"照片: {actor.profile_url}")
