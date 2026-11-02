<script lang="ts">
	import { Music2 } from 'lucide-svelte'
	import { formatTime } from '$lib/utils/time'
	import type { Playback } from './types'

	let {
		playback,
		showUI,
		showSquareCover
	}: {
		playback: Playback
		showUI: boolean
		showSquareCover: boolean
	} = $props()

	const activeLine = $derived(
		playback.activeIndex >= 0 ? playback.lines[playback.activeIndex] : null
	)
	const title = $derived(playback.track?.title ?? '')
</script>

{#if showSquareCover && playback.coverLarge}
	<img
		src={playback.coverLarge}
		alt=""
		referrerpolicy="no-referrer"
		class="absolute top-1/2 right-[7vw] aspect-square h-[min(72vh,42vw)] -translate-y-1/2 rounded-2xl object-cover shadow-[0_30px_80px_rgba(0,0,0,0.6)]"
	/>
{/if}

<div
	class="absolute top-6 left-6 flex w-80 items-center gap-3 rounded-lg border border-white/15 bg-white/10 p-2.5 shadow-2xl backdrop-blur-xl"
>
	{#if playback.coverSmall}
		<img
			src={playback.coverSmall}
			alt=""
			referrerpolicy="no-referrer"
			class="h-14 w-14 shrink-0 rounded-sm object-cover"
		/>
	{:else}
		<div class="grid h-14 w-14 shrink-0 place-items-center rounded-sm bg-white/10">
			<Music2 class="h-6 w-6 opacity-60" />
		</div>
	{/if}
	<div class="min-w-0 flex-1">
		<p class="truncate text-sm font-semibold">{title}</p>
		<div class="mt-2 flex items-center gap-2">
			<div class="h-1 flex-1 overflow-hidden rounded-full bg-white/25">
				<div class="h-full bg-white" style="width: {playback.progress * 100}%"></div>
			</div>
			<span class="font-mono text-[11px] text-white/80">{formatTime(playback.currentTime)}</span>
		</div>
	</div>
</div>

<div
	class="absolute left-10 transition-all duration-300 md:left-14 {showSquareCover
		? 'max-w-[44vw]'
		: 'max-w-[70vw]'} {showUI ? 'bottom-36' : 'bottom-16'}"
>
	{#if activeLine?.text}
		<p class="mb-3 text-lg text-white/80 drop-shadow-sm md:text-xl">{activeLine.text}</p>
	{/if}
	<h1
		class="line-clamp-2 leading-none font-black tracking-tight italic drop-shadow-[0_4px_24px_rgba(0,0,0,0.6)] {title.length >
		28
			? 'text-4xl md:text-5xl'
			: 'text-5xl md:text-7xl'}"
	>
		{title}
	</h1>
	<p class="mt-3 text-base text-white/70 drop-shadow-sm md:text-lg">
		{playback.track?.artist ?? ''}
	</p>
	<div class="mt-4 flex items-center gap-4">
		<div class="h-px w-[min(40vw,26rem)] bg-white/30">
			<div class="h-px bg-white" style="width: {playback.progress * 100}%"></div>
		</div>
		<span class="font-mono text-2xl font-light tracking-wider drop-shadow-sm">
			{formatTime(playback.totalTime - playback.currentTime)}
		</span>
	</div>
</div>
