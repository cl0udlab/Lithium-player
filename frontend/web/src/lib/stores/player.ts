import { writable } from 'svelte/store';
import type { MusicTrack, Video } from '$lib/types';
import type { MediaPlayerElement } from 'vidstack/elements';
import { playerliststat } from '$lib/stores/playerlist';

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

	const playMusiclist = async (track: MusicTrack[]) => {
		for (const t of track) {
			playerliststat.addmusic(t);
		}
		await playMusic(track[0]);
	};
	const playMusic = async (track: MusicTrack) => {
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
			currentState.player.addEventListener('ended', async () => {
				console.log('播放結束');
				await playNext();
			});
			await currentState.player.play();
		} catch (error) {
			console.error('播放失敗:', error);
			update((state) => ({ ...state, isPlaying: false }));
		}
	};

	const playNext = async () => {
		const tracks = playerliststat.gettracks();
		console.log(tracks);
		const currentIndex = tracks.findIndex((t) => t.id === currentState.currentTrack?.id);
		if (currentIndex < tracks.length - 1) {
			await playMusic(tracks[currentIndex + 1]);
		}
	};
	const playPrevious = async () => {
		const tracks = playerliststat.gettracks();
		const currentIndex = tracks.findIndex((t) => t.id === currentState.currentTrack?.id);
		if (currentIndex > 0) {
			await playMusic(tracks[currentIndex - 1]);
		}
	};
	return {
		subscribe,
		setPlayer: (player: MediaPlayerElement) => {
			playerliststat.resetlist();
			update((state) => ({ ...state, player }));
		},
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
		playNext,
		playPrevious,
		playMusic,
		playMusiclist,
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
