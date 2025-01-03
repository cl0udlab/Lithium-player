<script lang="ts">
	import { parseLyrics } from '$lib/utils/lyrics'
	import { onMount } from 'svelte'

	export let lyrics: string
	export let currentTime: number

	let lyricsContainer: HTMLDivElement

	$: parsedLyrics = parseLyrics(lyrics)
	$: currentIndex = parsedLyrics.findIndex(
		(line, i) =>
			currentTime >= line.time && (!parsedLyrics[i + 1] || currentTime < parsedLyrics[i + 1].time)
	)

	onMount(() => {
		if (currentIndex >= 0 && lyricsContainer) {
			const activeLine = lyricsContainer.children[currentIndex] as HTMLElement
			activeLine.scrollIntoView({ behavior: 'auto', block: 'center' })
		}
	})

	$: if (currentIndex >= 0 && lyricsContainer) {
		const activeLine = lyricsContainer.children[currentIndex] as HTMLElement
		activeLine.scrollIntoView({ behavior: 'smooth', block: 'center' })
	}
</script>

<div
	bind:this={lyricsContainer}
	class="flex h-[70vh] flex-col items-center justify-start space-y-2 overflow-y-auto scroll-smooth py-[35vh] text-lg"
>
	{#each parsedLyrics as line, i}
		<div
			class={`transition-all duration-300 ${
				i === currentIndex ? 'bg-primary scale-110 rounded px-2 py-1 text-white' : 'opacity-50'
			}`}
		>
			{line.text}
		</div>
	{/each}
</div>

<style>
	div::-webkit-scrollbar {
		display: none;
	}

	div {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}
</style>
