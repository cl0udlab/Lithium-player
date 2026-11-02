<script lang="ts">
	import LyricsScroller from './LyricsScroller.svelte'
	import type { Playback } from './types'

	let { playback, onSeek }: { playback: Playback; onSeek: (time: number) => void } = $props()

	function lineStyle(index: number) {
		const distance = Math.abs(index - Math.max(playback.activeIndex, 0))
		if (index === playback.activeIndex) return 'opacity-100 scale-100'
		if (distance === 1) return 'opacity-30 scale-[0.8]'
		if (distance === 2) return 'opacity-20 scale-[0.76] blur-[0.5px]'
		return 'opacity-10 scale-75 blur-[1px]'
	}
</script>

{#if playback.lines.length > 0}
	<LyricsScroller
		lines={playback.lines}
		activeIndex={playback.activeIndex}
		class="lyrics-mask absolute inset-x-0 bottom-32 top-12"
	>
		{#snippet line(item, i)}
			<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
			<div
				class="mx-auto max-w-4xl origin-center cursor-pointer px-8 py-4 text-center transition-all duration-500 ease-out hover:opacity-80 {lineStyle(
					i
				)}"
				onclick={() => onSeek(item.time)}
			>
				{#if item.text}
					<p class="text-3xl font-bold leading-snug tracking-wide md:text-5xl">{item.text}</p>
				{:else}
					<p class="text-2xl tracking-[0.5em] opacity-60">• • •</p>
				{/if}
				{#each item.translations as translation}
					<p class="mt-2 text-lg text-white/60 md:text-2xl">{translation}</p>
				{/each}
			</div>
		{/snippet}
	</LyricsScroller>
{:else}
	<div class="flex h-full flex-col items-center justify-center gap-4 px-8 pb-24 text-center">
		<h1 class="text-4xl font-bold md:text-6xl">{playback.track?.title ?? ''}</h1>
		<p class="text-xl text-white/60">{playback.track?.artist ?? ''}</p>
		<p class="mt-6 text-sm text-white/30">
			{playback.track?.lyrics == null ? '正在尋找歌詞…' : '沒有歌詞'}
		</p>
	</div>
{/if}

<style>
	:global(.lyrics-mask) {
		mask-image: linear-gradient(to bottom, transparent, black 20%, black 80%, transparent);
	}
</style>
