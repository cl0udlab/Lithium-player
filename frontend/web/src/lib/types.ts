export interface Playlist {
	tracks: MusicTrack[]
}
export interface MusicTrack {
	id: number
	title: string
	artist: string
	album: string
	cover_art: string
  lyrics: string
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
