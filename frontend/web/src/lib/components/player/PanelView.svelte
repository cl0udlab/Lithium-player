<script lang="ts">
	import { ChevronLeft, ChevronRight, Play, Pause, Music2 } from 'lucide-svelte'
	import { playerState } from '$lib/stores/player'
	import { formatTime } from '$lib/utils/time'
	import LyricsScroller from './LyricsScroller.svelte'
	import type { Playback } from './types'

	let {
		playback,
		volume,
		onSeek,
		onTogglePlay,
		onVolume
	}: {
		playback: Playback
		volume: number
		onSeek: (time: number) => void
		onTogglePlay: () => void
		onVolume: (volume: number) => void
	} = $props()
</script>

<div
	class="absolute top-16 bottom-0 left-10 w-[min(26rem,34vw)] bg-white/25 text-neutral-900 shadow-2xl backdrop-blur-md"
>
	<span class="absolute -top-1 -left-1 h-2.5 w-2.5 bg-black"></span>
	<span class="absolute -top-1 -right-1 h-2.5 w-2.5 bg-black"></span>
	<span class="absolute -bottom-1 -left-1 h-2.5 w-2.5 bg-black"></span>
	<span class="absolute -right-1 -bottom-1 h-2.5 w-2.5 bg-black"></span>

	<div class="flex h-full flex-col overflow-y-auto px-8 pt-10 pb-8">
		<div class="relative mx-3">
			<span class="absolute -top-3 -left-3 h-9 w-9 border-t-2 border-l-2 border-neutral-900"></span>
			<span class="absolute -top-3 -right-3 h-9 w-9 border-t-2 border-r-2 border-neutral-900"
			></span>
			<span class="absolute -bottom-3 -left-3 h-9 w-9 border-b-2 border-l-2 border-neutral-900"
			></span>
			<span class="absolute -right-3 -bottom-3 h-9 w-9 border-r-2 border-b-2 border-neutral-900"
			></span>
			{#if playback.coverLarge}
				<img
					src={playback.coverLarge}
					alt=""
					referrerpolicy="no-referrer"
					class="aspect-square w-full object-cover shadow-lg"
				/>
			{:else}
				<div class="grid aspect-square w-full place-items-center bg-white/40">
					<Music2 class="h-16 w-16 opacity-40" />
				</div>
			{/if}
		</div>

		<h2 class="mt-10 truncate border-l-4 border-neutral-900 pl-3 text-2xl font-bold">
			{playback.track?.title ?? ''}
		</h2>
		<p class="mt-2 truncate text-xs text-neutral-900/50">{playback.track?.artist ?? ''}</p>

		<div class="mt-8 flex justify-between font-mono text-xs">
			<span>{formatTime(playback.currentTime)}</span>
			<span>{formatTime(playback.totalTime)}</span>
		</div>
		<div class="relative mt-1 h-2.5 border border-neutral-900/70">
			<div class="h-full bg-neutral-900" style="width: {playback.progress * 100}%"></div>
			<input
				type="range"
				min="0"
				max={playback.totalTime || 0}
				step="0.1"
				value={playback.currentTime}
				oninput={(e) => onSeek(Number(e.currentTarget.value))}
				class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
				aria-label="播放進度"
			/>
		</div>

		<div class="mt-10 flex items-center justify-around">
			<button
				class="transition-transform hover:scale-110 active:scale-95"
				onclick={() => playerState.playPrevious()}
				aria-label="上一首"
			>
				<ChevronLeft class="h-11 w-11" strokeWidth={1.25} />
			</button>
			<button
				class="transition-transform hover:scale-110 active:scale-95"
				onclick={onTogglePlay}
				aria-label={playback.isPlaying ? '暫停' : '播放'}
			>
				{#if playback.isPlaying}
					<Pause class="h-11 w-11" strokeWidth={1.25} />
				{:else}
					<Play class="h-11 w-11" strokeWidth={1.25} />
				{/if}
			</button>
			<button
				class="transition-transform hover:scale-110 active:scale-95"
				onclick={() => playerState.playNext()}
				aria-label="下一首"
			>
				<ChevronRight class="h-11 w-11" strokeWidth={1.25} />
			</button>
		</div>

		<div class="mt-auto pt-10">
			<div class="relative h-2.5 border border-neutral-900/70">
				<div class="h-full bg-neutral-900" style="width: {volume * 100}%"></div>
				<input
					type="range"
					min="0"
					max="1"
					step="0.01"
					value={volume}
					oninput={(e) => onVolume(Number(e.currentTarget.value))}
					class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
					aria-label="音量"
				/>
			</div>
			<div class="mt-1 flex justify-between font-mono text-xs">
				<span>VOLUME</span>
				<span>{Math.round(volume * 100)}</span>
			</div>
		</div>
	</div>
</div>

{#if playback.lines.length > 0}
	<LyricsScroller
		lines={playback.lines}
		activeIndex={playback.activeIndex}
		anchor={0.4}
		class="lyrics-mask absolute top-0 right-0 bottom-0 left-[calc(min(26rem,34vw)+5rem)]"
	>
		{#snippet line(item, i)}
			{@const active = i === playback.activeIndex}
			<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
			<div
				class="mr-16 cursor-pointer py-4 pr-8 pl-14 transition-all duration-300 {active
					? 'bg-black text-white shadow-2xl'
					: 'hover:blur-0 text-white/45 blur-[1.2px] hover:text-white/70'}"
				onclick={() => onSeek(item.time)}
			>
				<p class="text-2xl font-bold drop-shadow-sm md:text-3xl">{item.text || '• • •'}</p>
				{#each item.translations as translation}
					<p class="mt-1 text-sm font-bold drop-shadow-sm md:text-base">{translation}</p>
				{/each}
			</div>
		{/snippet}
	</LyricsScroller>
{:else}
	<div
		class="absolute top-0 right-0 bottom-0 left-[calc(min(26rem,34vw)+5rem)] flex items-center pl-14 text-xl text-white/50"
	>
		{playback.track?.lyrics == null ? '正在尋找歌詞…' : '沒有歌詞'}
	</div>
{/if}
