<script lang="ts">
	import {
		Play,
		Pause,
		SkipBack,
		SkipForward,
		ChevronDown,
		Maximize,
		Minimize,
		Settings2
	} from 'lucide-svelte'
	import { onMount } from 'svelte'
	import { playerState } from '$lib/stores/player'
	import { playerSettings, resolveBackgroundUrl } from '$lib/stores/playerSettings'
	import { coverUrl } from '$lib/api'
	import { parseLyrics, currentLyricIndex } from '$lib/utils/lyrics'
	import { formatTime } from '$lib/utils/time'
	import type { PlayableTrack } from '$lib/types'
	import type { Playback } from './player/types'
	import LyricsView from './player/LyricsView.svelte'
	import ArtView from './player/ArtView.svelte'
	import PanelView from './player/PanelView.svelte'
	import SettingsMenu from './player/SettingsMenu.svelte'

	let { player, onClose }: { player: HTMLAudioElement | null; onClose: () => void } = $props()

	const HIDE_UI_DELAY = 3000

	let currentTime = $state(0)
	let duration = $state(0)
	let isPlaying = $state(false)
	let showUI = $state(true)
	let settingsOpen = $state(false)
	let isFullscreen = $state(false)
	let isWideCover = $state(true)

	const track = $derived($playerState.currentTrack as PlayableTrack | null)
	const lines = $derived(parseLyrics(track?.lyrics ?? ''))
	const totalTime = $derived(duration || (track && 'duration' in track ? track.duration : 0) || 0)
	const coverLarge = $derived(coverUrl(track?.cover_art, 1600))

	const playback: Playback = $derived({
		track,
		lines,
		activeIndex: currentLyricIndex(lines, currentTime),
		currentTime,
		totalTime,
		progress: totalTime ? Math.min(currentTime / totalTime, 1) : 0,
		isPlaying,
		coverSmall: coverUrl(track?.cover_art, 300),
		coverLarge
	})

	const view = $derived(
		$playerSettings.mode === 'lyrics' ? 'lyrics' : $playerSettings.artLyrics ? 'panel' : 'art'
	)
	const customBackground = $derived(
		$playerSettings.background.source === 'custom' && $playerSettings.background.url
			? resolveBackgroundUrl($playerSettings.background.url)
			: null
	)
	const backgroundUrl = $derived(customBackground ?? coverLarge)
	const backgroundType = $derived(customBackground ? $playerSettings.background.type : 'image')

	const sharpBackground = $derived(view !== 'lyrics' && (!!customBackground || isWideCover))
	const overlay = $derived(
		view === 'lyrics' ? 'bg-black/60' : view === 'panel' ? 'bg-black/15' : 'bg-black/0'
	)

	$effect(() => {
		if (!player) return
		const audio = player
		let frame = 0
		const sync = () => {
			currentTime = audio.currentTime || 0
			duration = Number.isFinite(audio.duration) ? audio.duration : 0
			isPlaying = !audio.paused
		}
		const loop = () => {
			sync()
			frame = requestAnimationFrame(loop)
		}
		const onPlay = () => {
			sync()
			cancelAnimationFrame(frame)
			frame = requestAnimationFrame(loop)
		}
		const onPause = () => {
			cancelAnimationFrame(frame)
			sync()
		}
		sync()
		if (!audio.paused) onPlay()
		const events = ['durationchange', 'loadedmetadata', 'seeked', 'timeupdate'] as const
		events.forEach((e) => audio.addEventListener(e, sync))
		audio.addEventListener('play', onPlay)
		audio.addEventListener('pause', onPause)
		return () => {
			cancelAnimationFrame(frame)
			events.forEach((e) => audio.removeEventListener(e, sync))
			audio.removeEventListener('play', onPlay)
			audio.removeEventListener('pause', onPause)
		}
	})

	let hideTimer: ReturnType<typeof setTimeout>
	function wakeUI() {
		showUI = true
		clearTimeout(hideTimer)
		hideTimer = setTimeout(() => {
			if (isPlaying && !settingsOpen) showUI = false
		}, HIDE_UI_DELAY)
	}

	onMount(() => {
		wakeUI()
		const onFullscreenChange = () => (isFullscreen = !!document.fullscreenElement)
		document.addEventListener('fullscreenchange', onFullscreenChange)
		return () => {
			clearTimeout(hideTimer)
			document.removeEventListener('fullscreenchange', onFullscreenChange)
			if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
		}
	})

	function togglePlay() {
		if (!player) return
		if (player.paused) player.play()
		else player.pause()
	}

	function seekTo(time: number) {
		if (!player) return
		player.currentTime = Math.max(0, Math.min(time, totalTime || time))
		currentTime = player.currentTime
	}

	function setVolume(volume: number) {
		playerSettings.patch({ volume })
	}

	function toggleFullscreen() {
		if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
		else document.documentElement.requestFullscreen().catch(() => {})
	}

	function onKeydown(e: KeyboardEvent) {
		if ((e.target as HTMLElement)?.closest('input[type=text], input[type=url], textarea')) return
		wakeUI()
		switch (e.key) {
			case ' ':
				e.preventDefault()
				togglePlay()
				break
			case 'ArrowLeft':
				seekTo(currentTime - 5)
				break
			case 'ArrowRight':
				seekTo(currentTime + 5)
				break
			case 'l':
			case 'L':
				playerSettings.patch({ mode: $playerSettings.mode === 'lyrics' ? 'art' : 'lyrics' })
				break
			case 'f':
			case 'F':
				toggleFullscreen()
				break
			case 'Escape':
				if (settingsOpen) settingsOpen = false
				else if (!document.fullscreenElement) onClose()
				break
		}
	}

	function onCoverLoad(e: Event) {
		if (customBackground) return
		const img = e.currentTarget as HTMLImageElement
		isWideCover = img.naturalWidth / img.naturalHeight >= 1.4
	}

	const roundButton =
		'grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-black/45 text-white/70 backdrop-blur-xl transition-colors hover:bg-black/70 hover:text-white'
</script>

<svelte:window onkeydown={onKeydown} />

<!-- svelte-ignore a11y_no_static_element_interactions, a11y_click_events_have_key_events -->
<div
	class="fixed inset-0 z-[60] overflow-hidden bg-[#050507] text-white select-none {showUI
		? ''
		: 'cursor-none'}"
	onpointermove={wakeUI}
	onpointerdown={wakeUI}
	onclick={() => (settingsOpen = false)}
>
	<!-- 背景 -->
	<div class="absolute inset-0" style="filter: brightness({$playerSettings.brightness})">
		{#if backgroundUrl}
			{#key backgroundUrl}
				{#if backgroundType === 'video'}
					<video
						src={backgroundUrl}
						autoplay
						muted
						loop
						playsinline
						class="absolute inset-0 h-full w-full object-cover transition-[filter,transform] duration-700 {sharpBackground
							? ''
							: 'scale-110 blur-2xl'}"
					></video>
				{:else}
					<img
						src={backgroundUrl}
						alt=""
						referrerpolicy="no-referrer"
						onload={onCoverLoad}
						class="absolute inset-0 h-full w-full object-cover transition-[filter,transform] duration-700 {sharpBackground
							? ''
							: 'scale-125 blur-3xl'}"
					/>
				{/if}
			{/key}
		{/if}
		<div class="absolute inset-0 transition-colors duration-700 {overlay}"></div>
		<div class="vignette absolute inset-0 {view === 'art' ? 'vignette-art' : ''}"></div>
	</div>

	{#key view}
		<div class="fade-in absolute inset-0">
			{#if view === 'lyrics'}
				<LyricsView {playback} onSeek={seekTo} />
			{:else if view === 'art'}
				<ArtView {playback} {showUI} showSquareCover={!customBackground && !isWideCover} />
			{:else}
				<PanelView
					{playback}
					volume={$playerSettings.volume}
					onSeek={seekTo}
					onTogglePlay={togglePlay}
					onVolume={setVolume}
				/>
			{/if}
		</div>
	{/key}

	{#if view !== 'panel'}
		<div
			class="absolute bottom-8 left-1/2 flex w-[min(80vw,30rem)] -translate-x-1/2 items-center gap-4 rounded-full border border-white/10 bg-black/55 py-2.5 pr-5 pl-2.5 shadow-2xl backdrop-blur-xl transition-all duration-300 {showUI
				? 'translate-y-0 opacity-100'
				: 'pointer-events-none translate-y-4 opacity-0'}"
		>
			<button
				class="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-white text-black transition-transform hover:scale-105 active:scale-95"
				onclick={togglePlay}
				aria-label={isPlaying ? '暫停' : '播放'}
			>
				{#if isPlaying}
					<Pause class="h-5 w-5" fill="currentColor" />
				{:else}
					<Play class="ml-0.5 h-5 w-5" fill="currentColor" />
				{/if}
			</button>

			<div class="min-w-0 flex-1">
				<div class="flex items-center justify-center gap-2">
					<button
						class="text-white/50 transition-colors hover:text-white"
						onclick={() => playerState.playPrevious()}
						aria-label="上一首"
					>
						<SkipBack class="h-3.5 w-3.5" fill="currentColor" />
					</button>
					<p class="truncate text-sm font-semibold">{track?.title ?? ''}</p>
					<button
						class="text-white/50 transition-colors hover:text-white"
						onclick={() => playerState.playNext()}
						aria-label="下一首"
					>
						<SkipForward class="h-3.5 w-3.5" fill="currentColor" />
					</button>
				</div>
				<div class="mt-1.5 flex items-center gap-3 font-mono text-[10px] text-white/50">
					<span>{formatTime(currentTime)}</span>
					<input
						type="range"
						min="0"
						max={totalTime || 0}
						step="0.1"
						value={currentTime}
						oninput={(e) => seekTo(Number(e.currentTarget.value))}
						class="pill-range flex-1"
						style="--progress: {playback.progress * 100}%"
						aria-label="播放進度"
					/>
					<span>{formatTime(totalTime)}</span>
				</div>
			</div>
		</div>
	{/if}

	<div
		class="absolute right-6 bottom-8 flex items-center gap-2 transition-all duration-300 {showUI ||
		settingsOpen
			? 'opacity-100'
			: 'pointer-events-none opacity-0'}"
	>
		<button
			class="{roundButton} {settingsOpen
				? 'bg-white text-black hover:bg-white hover:text-black'
				: ''}"
			onclick={(e) => {
				e.stopPropagation()
				settingsOpen = !settingsOpen
			}}
			title="顯示設定"
		>
			<Settings2 class="h-4 w-4" />
		</button>
		<button class={roundButton} onclick={toggleFullscreen} title="全螢幕 (F)">
			{#if isFullscreen}
				<Minimize class="h-4 w-4" />
			{:else}
				<Maximize class="h-4 w-4" />
			{/if}
		</button>
		<button class={roundButton} onclick={onClose} title="收起 (Esc)">
			<ChevronDown class="h-4 w-4" />
		</button>
	</div>

	{#if settingsOpen}
		<SettingsMenu />
	{/if}
</div>

<style>
	.vignette {
		background: radial-gradient(ellipse at center, transparent 35%, rgba(0, 0, 0, 0.65) 100%);
	}

	.vignette-art {
		background:
			linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent 45%),
			linear-gradient(to bottom, rgba(0, 0, 0, 0.35), transparent 25%);
	}

	.fade-in {
		animation: fade-in 0.5s ease-out;
	}
	@keyframes fade-in {
		from {
			opacity: 0;
		}
	}

	.pill-range {
		appearance: none;
		height: 4px;
		border-radius: 9999px;
		background: linear-gradient(
			to right,
			white var(--progress),
			rgba(255, 255, 255, 0.2) var(--progress)
		);
		cursor: pointer;
	}
	.pill-range::-webkit-slider-thumb {
		appearance: none;
		width: 10px;
		height: 10px;
		border-radius: 9999px;
		background: white;
		opacity: 0;
		transition: opacity 0.2s;
	}
	.pill-range:hover::-webkit-slider-thumb {
		opacity: 1;
	}
	.pill-range::-moz-range-thumb {
		width: 10px;
		height: 10px;
		border: none;
		border-radius: 9999px;
		background: white;
	}
</style>
