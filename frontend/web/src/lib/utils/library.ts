import { apiFetch } from '$lib/api'
import type { MusicTrack } from '$lib/types'

export async function fetchAlbumTracks(albumId: number): Promise<MusicTrack[]> {
	const response = await apiFetch(`/file/album?album_id=${albumId}`)
	if (!response.ok) return []
	const album = await response.json()
	return ((album.tracks ?? []) as MusicTrack[])
		.map((t) => ({ ...t, kind: 'music' as const }))
		.sort(
			(a: any, b: any) =>
				(a.disc_number ?? 0) - (b.disc_number ?? 0) || (a.track_number ?? 0) - (b.track_number ?? 0)
		)
}

export function formatDuration(seconds: number): string {
	if (!seconds) return ''
	const h = Math.floor(seconds / 3600)
	const m = Math.floor((seconds % 3600) / 60)
	const s = Math.floor(seconds % 60)
	const mm = h ? m.toString().padStart(2, '0') : `${m}`
	return `${h ? `${h}:` : ''}${mm}:${s.toString().padStart(2, '0')}`
}

export const platformLabel: Record<string, string> = {
	youtube: 'YouTube',
	bilibili: 'Bilibili',
	soundcloud: 'SoundCloud',
	unknown: '網路'
}
