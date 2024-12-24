export interface Playlist {
	id: string;
	name: string;
	tracks: number[];
	createdAt: number;
}
export interface MusicTrack {
	id: number;
	title: string;
	artist: string;
	album: string;
	albumArt: string;
}

export interface Video {
	id: number;
	title: string;
	description: string;
}

export interface Filei {
	id: number;
	filepath: string;
	file_format: string;
}
