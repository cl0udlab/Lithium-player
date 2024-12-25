import { writable } from 'svelte/store';
import type { Playlist, MusicTrack } from '$lib/types';

const initplaylist: Playlist = {
	tracks: []
};

function createPlayerlistStore() {
	const { subscribe, set, update } = writable<Playlist>();

	const syncfromlocal = () => {
		const savedStars = localStorage.getItem('stars');
		if (!savedStars) {
			const initialStars: Playlist = initplaylist;
			localStorage.setItem('stars', JSON.stringify(initialStars));
			set(initialStars);
		} else {
			set(JSON.parse(savedStars));
		}
	};

	return {
		subscribe,
		initialize: () => {
			const savedStars = localStorage.getItem('stars');
			if (!savedStars) {
				const initialStars: Playlist = initplaylist;
				localStorage.setItem('stars', JSON.stringify(initialStars));
				set(initialStars);
			} else {
				set(JSON.parse(savedStars));
			}
		},
		gettracks: () => {
      syncfromlocal();
			let tracks: MusicTrack[] = [];
			subscribe((state) => {
				tracks = state?.tracks || [];
			})();
			return tracks;
		},
		resetlist: () => {
			localStorage.setItem('stars', JSON.stringify(initplaylist));
			set(initplaylist);
		},
		addmusic: (track: MusicTrack) => {
			update((state) => {
				if (!state) {
					return { tracks: [track] };
				}
				localStorage.setItem('stars', JSON.stringify({ tracks: [...(state.tracks || []), track] }));
				return {
					tracks: [...(state.tracks || []), track]
				};
			});
		}
	};
}

export const playerliststat = createPlayerlistStore();
