import { writable } from 'svelte/store'
import type { PlayableTrack, Video } from '$lib/types'
import { isStreamTrack, trackKey } from '$lib/types'
import { playerliststat } from '$lib/stores/playerlist'
import { APIUrl } from '$lib/api'

interface PlayerState {
	type: 'video' | 'audio' | null
	isPlaying: boolean
	currentTrack: PlayableTrack | Video | null
	currentTime: number
	src: string | null
	player: HTMLAudioElement | null
	isExpanded: boolean
}

const initialState: PlayerState = {
	type: null,
	isPlaying: false,
	currentTrack: null,
	currentTime: 0,
	src: null,
	player: null,
	isExpanded: false
}

function trackSrc(track: PlayableTrack) {
	return isStreamTrack(track)
		? `${APIUrl}/stream/stream/${track.id}`
		: `${APIUrl}/stream/music/${track.id}`
}

function createPlayerState() {
	const { subscribe, update } = writable<PlayerState>(initialState)
	let currentState: PlayerState = initialState
	subscribe((state) => {
		currentState = state
	})
	let boundPlayer: HTMLAudioElement | null = null

	const bindPlayerEvents = (player: HTMLAudioElement) => {
		if (boundPlayer === player) return
		boundPlayer = player
		player.addEventListener('timeupdate', () => {
			update((state) => ({ ...state, currentTime: player.currentTime || 0 }))
		})
		player.addEventListener('ended', async () => {
			await playNext()
		})
	}


	const loadLyrics = async (track: PlayableTrack) => {
		const path = isStreamTrack(track) ? 'stream' : 'music'
		try {
			const response = await fetch(`${APIUrl}/stream/${path}/${track.id}/lyrics`)
			if (!response.ok) return
			const { lyrics } = await response.json()
			track.lyrics = lyrics ?? ''
			update((state) =>
				state.currentTrack && trackKey(state.currentTrack as PlayableTrack) === trackKey(track)
					? { ...state, currentTrack: { ...track } }
					: state
			)
		} catch (error) {
			console.error('取得歌詞失敗:', error)
		}
	}

	const playMusiclist = async (tracks: PlayableTrack[], startIndex = 0) => {
		for (const t of tracks) {
			playerliststat.addmusic(t)
		}
		await playMusic(tracks[startIndex])
	}
	const playMusic = async (track: PlayableTrack) => {
		update((state) => ({
			...state,
			currentTrack: track,
			isPlaying: true,
			type: 'audio'
		}))
		if (!currentState.player) {
			console.error('播放器初始化失敗')
			return
		}
		const player = currentState.player
		bindPlayerEvents(player)
		if (track.lyrics == null) {
			loadLyrics(track)
		}
		try {
			player.src = trackSrc(track)
			await new Promise<void>((resolve, reject) => {
				const onCanPlay = () => {
					player.removeEventListener('canplay', onCanPlay)
					player.removeEventListener('error', onError)
					resolve()
				}
				const onError = (error: any) => {
					player.removeEventListener('canplay', onCanPlay)
					player.removeEventListener('error', onError)
					reject(error)
				}
				player.addEventListener('canplay', onCanPlay)
				player.addEventListener('error', onError)
			})
			await player.play()
		} catch (error) {
			console.error('播放失敗:', error)
			update((state) => ({ ...state, isPlaying: false }))
		}
	}

	const currentIndex = (tracks: PlayableTrack[]) => {
		const current = currentState.currentTrack
		if (!current || !('artist' in current)) return -1
		const key = trackKey(current as PlayableTrack)
		return tracks.findIndex((t) => trackKey(t) === key)
	}

	const playNext = async () => {
		const tracks = playerliststat.gettracks()
		const index = currentIndex(tracks)
		if (index < tracks.length - 1) {
			await playMusic(tracks[index + 1])
		}
	}
	const playPrevious = async () => {
		const tracks = playerliststat.gettracks()
		const index = currentIndex(tracks)
		if (index > 0) {
			await playMusic(tracks[index - 1])
		}
	}
	return {
		subscribe,
		setPlayer: (player: HTMLAudioElement) => {
			playerliststat.resetlist()
			update((state) => ({ ...state, player }))
		},
		toggleExpanded: () => update((state) => ({ ...state, isExpanded: !state.isExpanded })),
		setExpanded: (value: boolean) => update((state) => ({ ...state, isExpanded: value })),
		getPlayer: () => {
			let player
			update((state) => {
				player = state.player
				return state
			})
			return player
		},
		playNext,
		playPrevious,
		playMusic,
		playMusiclist,
		stop: () =>
			update((state) => {
				if (state.player) {
					state.player.pause()
				}
				return { ...state, isPlaying: false }
			}),
		getCurrentTime: () => currentState.currentTime,
		setCurrentTime: (time: number) =>
			update((state) => {
				if (state.player) {
					state.player.currentTime = time
				}
				return { ...state, currentTime: time }
			})
	}
}

export const playerState = createPlayerState()
