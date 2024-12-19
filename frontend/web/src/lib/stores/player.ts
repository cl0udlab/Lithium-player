import { writable } from 'svelte/store';
import type { MusicTrack } from '$lib/types';

interface PlayerState {
	isPlaying: boolean;
	currentTrack: MusicTrack | null;
	src: string | null;
	isExpanded: boolean;
}

const initialState: PlayerState = {
	isPlaying: false,
	currentTrack: null,
	src: null,
	isExpanded: false
};

export const playerState = writable<PlayerState>(initialState);
