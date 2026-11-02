export interface Playlist {
	tracks: PlayableTrack[]
}
export interface MusicTrack {
	id: number
	title: string
	artist: string
	album: string
	cover_art: string
	lyrics: string
	kind?: 'music'
}

export interface StreamTrack {
	id: number
	title: string
	artist: string
	url: string
	platform: 'youtube' | 'bilibili' | 'soundcloud' | 'unknown'
	duration: number
	cover_art: string | null
	lyrics: string | null
	kind: 'stream'
}

export type PlayableTrack = MusicTrack | StreamTrack

export function isStreamTrack(track: unknown): track is StreamTrack {
	return (track as StreamTrack | null)?.kind === 'stream'
}

export function trackKey(track: PlayableTrack): string {
	return `${track.kind ?? 'music'}-${track.id}`
}

export interface Video {
	id: number
	title: string
	description: string
}

export interface Filei {
	id: number
	filepath: string
	file_format: string
}

export type IconComponent = typeof import('lucide-svelte').Music
