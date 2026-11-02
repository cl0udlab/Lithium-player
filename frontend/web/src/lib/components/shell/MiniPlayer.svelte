<script lang="ts">
	import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Maximize2, Disc3 } from 'lucide-svelte'
	import { playerState } from '$lib/stores/player'
	import { playerSettings } from '$lib/stores/playerSettings'
	import { coverUrl } from '$lib/api'
	import { formatTime } from '$lib/utils/time'
	import type { PlayableTrack } from '$lib/types'
	import Slider from '$lib/components/ui/Slider.svelte'

	let { player, onExpand }: { player: HTMLAudioElement | null; onExpand: () => void } = $props()

	let currentTime = $state(0)
	let duration = $state(0)
	let isPlaying = $state(false)
	let lastVolume = 1

	const track = $derived($playerState.currentTrack as PlayableTrack | null)
	const cover = $derived(coverUrl(track?.cover_art, 160))
	const muted = $derived($playerSettings.volume === 0)

	$effect(() => {
		if (!player) return
		const audio = player
		const sync = () => {
			currentTime = audio.currentTime || 0
			duration = Number.isFinite(audio.duration) ? audio.duration : 0
			isPlaying = !audio.paused
		}
		sync()
		const events = ['timeupdate', 'durationchange', 'loadedmetadata', 'play', 'pause', 'seeked']
		events.forEach((e) => audio.addEventListener(e, sync))
		return () => events.forEach((e) => audio.removeEventListener(e, sync))
	})

	function togglePlay() {
		if (!player) return
		if (player.paused) player.play()
		else player.pause()
	}

	function toggleMute() {
		if (muted) playerSettings.patch({ volume: lastVolume || 1 })
		else {
			lastVolume = $playerSettings.volume
			playerSettings.patch({ volume: 0 })
		}
	}
</script>

<div
	class="grid h-[76px] grid-cols-[minmax(0,1fr)_minmax(0,2fr)_minmax(0,1fr)] items-center gap-4 rounded-2xl border border-line/10 bg-surface px-3"
>
	<!-- 曲目資訊 -->
	<button class="flex min-w-0 items-center gap-3 text-left" onclick={onExpand} title="展開播放器">
		<div class="relative h-14 w-14 shrink-0 overflow-hidden rounded-lg bg-surface-3">
			{#if cover}
				<img src={cover} alt="" referrerpolicy="no-referrer" class="h-full w-full object-cover" />
			{:else}
				<Disc3 class="m-auto h-full w-6 text-fg-subtle" />
			{/if}
		</div>
		<div class="min-w-0">
			<p class="truncate text-sm font-semibold">{track?.title ?? ''}</p>
			<p class="truncate text-xs text-fg-muted">{track?.artist ?? ''}</p>
		</div>
	</button>

	<!-- 控制 + 進度 -->
	<div class="flex flex-col items-center gap-1">
		<div class="flex items-center gap-3">
			<button
				class="grid h-8 w-8 place-items-center rounded-full text-fg-muted hover:text-fg"
				onclick={() => playerState.playPrevious()}
				aria-label="上一首"
			>
				<SkipBack class="h-4 w-4" fill="currentColor" />
			</button>
			<button
				class="grid h-9 w-9 place-items-center rounded-full bg-fg text-bg transition-transform hover:scale-105 active:scale-95"
				onclick={togglePlay}
				aria-label={isPlaying ? '暫停' : '播放'}
			>
				{#if isPlaying}
					<Pause class="h-4 w-4" fill="currentColor" />
				{:else}
					<Play class="ml-0.5 h-4 w-4" fill="currentColor" />
				{/if}
			</button>
			<button
				class="grid h-8 w-8 place-items-center rounded-full text-fg-muted hover:text-fg"
				onclick={() => playerState.playNext()}
				aria-label="下一首"
			>
				<SkipForward class="h-4 w-4" fill="currentColor" />
			</button>
		</div>
		<div class="flex w-full max-w-xl items-center gap-2 font-mono text-[10px] text-fg-subtle">
			<span class="w-9 text-right">{formatTime(currentTime)}</span>
			<Slider
				value={currentTime}
				max={duration || 1}
				step={0.5}
				label="播放進度"
				onchange={(t) => player && (player.currentTime = t)}
			/>
			<span class="w-9">{formatTime(duration)}</span>
		</div>
	</div>

	<!-- 音量 + 展開 -->
	<div class="flex items-center justify-end gap-2">
		<button
			class="grid h-8 w-8 place-items-center rounded-full text-fg-muted hover:text-fg"
			onclick={toggleMute}
			aria-label={muted ? '取消靜音' : '靜音'}
		>
			{#if muted}
				<VolumeX class="h-4 w-4" />
			{:else}
				<Volume2 class="h-4 w-4" />
			{/if}
		</button>
		<Slider
			class="hidden max-w-28 md:flex"
			value={$playerSettings.volume}
			label="音量"
			onchange={(volume) => playerSettings.patch({ volume })}
		/>
		<button
			class="grid h-8 w-8 place-items-center rounded-full text-fg-muted hover:text-fg"
			onclick={onExpand}
			aria-label="展開播放器"
		>
			<Maximize2 class="h-4 w-4" />
		</button>
	</div>
</div>
