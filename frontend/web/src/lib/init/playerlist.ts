import { writable } from 'svelte/store';
import type { Playlist } from '$lib/types';

function createStarsStore() {
	const { subscribe, set, update } = writable<Playlist[]>([]);

	return {
		subscribe,
		initialize: () => {
			const savedStars = localStorage.getItem('stars');
			if (!savedStars) {
				const initialStars: Playlist[] = [];
				localStorage.setItem('stars', JSON.stringify(initialStars));
				set(initialStars);
			} else {
				set(JSON.parse(savedStars));
			}
		},
		addPlaylist: (name: string) => {
			update((lists) => {
				const newList: Playlist = {
					id: crypto.randomUUID(),
					name,
					tracks: [],
					createdAt: Date.now()
				};
				const updated = [...lists, newList];
				localStorage.setItem('stars', JSON.stringify(updated));
				return updated;
			});
		}
	};
}

export const stars = createStarsStore();
