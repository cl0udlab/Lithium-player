import { writable } from 'svelte/store';
import type { MusicTrack, Video } from '$lib/types';
import type { MediaPlayerElement } from 'vidstack/elements';

interface PlayerState {
	type: 'video' | 'audio' | null;
	isPlaying: boolean;
	currentTrack: MusicTrack | Video | null;
	src: string | null;
	player: MediaPlayerElement | null;
	isExpanded: boolean;
}

const initialState: PlayerState = {
	type: null,
	isPlaying: false,
	currentTrack: null,
	src: null,
	player: null,
	isExpanded: false
};

function createPlayerState() {
	const { subscribe, update } = writable<PlayerState>(initialState);
	let currentState: PlayerState = initialState;
	subscribe((state) => {
		currentState = state;
	});
	return {
		subscribe,
		setPlayer: (player: MediaPlayerElement) => update((state) => ({ ...state, player })),
		toggleExpanded: () => update((state) => ({ ...state, isExpanded: !state.isExpanded })),
		setExpanded: (value: boolean) => update((state) => ({ ...state, isExpanded: value })),
		getPlayer: () => {
			let player;
			update((state) => {
				player = state.player;
				return state;
			});
			return player;
		},
		play: (media: MusicTrack | Video, type: 'video' | 'audio') =>
			update((state) => {
				if (state.player && state.type != type) {
					state.player.pause();
				}
				return { ...state, type, currentTrack: media, isPlaying: true };
			}),
		async playMusic(track: MusicTrack) {
			subscribe((state) => {
				currentState = state;
			})();

			update((state) => ({
				...state,
				currentTrack: track,
				isPlaying: true,
				type: 'audio'
			}));
			if (!currentState.player) {
				console.error('播放器初始化失敗');
				return;
			}
			try {
				currentState.player.src = `http://localhost:8000/stream/music/${track.id}`;

				await new Promise<void>((resolve, reject) => {
					const onCanPlay = () => {
						currentState.player?.removeEventListener('can-play', onCanPlay);
						resolve();
					};

					const onError = (error: any) => {
						currentState.player?.removeEventListener('error', onError);
						reject(error);
					};

					currentState.player?.addEventListener('can-play', onCanPlay);
					currentState.player?.addEventListener('error', onError);
				});

				await currentState.player.play();
			} catch (error) {
				console.error('播放失敗:', error);
				update((state) => ({ ...state, isPlaying: false }));
			}
		},
		stop: () =>
			update((state) => {
				if (state.player) {
					state.player.pause();
				}
				return { ...state, isPlaying: false };
			})
	};
}

export const playerState = createPlayerState();
// export const playerState = writable<PlayerState>(initialState);
