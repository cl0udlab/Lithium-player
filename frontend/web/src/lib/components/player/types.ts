import type { PlayableTrack } from '$lib/types'
import type { LyricLine } from '$lib/utils/lyrics'

export interface Playback {
	track: PlayableTrack | null
	lines: LyricLine[]
	activeIndex: number
	currentTime: number
	totalTime: number
	progress: number
	isPlaying: boolean
	coverSmall: string | null
	coverLarge: string | null
}
