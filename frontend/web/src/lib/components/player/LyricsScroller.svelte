<script lang="ts">
	import type { Snippet } from 'svelte'
	import type { LyricLine } from '$lib/utils/lyrics'

	let {
		lines,
		activeIndex,
		anchor = 0.5,
		class: className = '',
		line
	}: {
		lines: LyricLine[]
		activeIndex: number
		anchor?: number
		class?: string
		line: Snippet<[LyricLine, number]>
	} = $props()

	let box = $state<HTMLDivElement>()
	let lineEls = $state<HTMLDivElement[]>([])
	let height = $state(0)
	let offset = $state(0)

	$effect(() => {
		const el = lineEls[Math.max(activeIndex, 0)]
		if (!el || !height) return
		offset = height * anchor - (el.offsetTop + el.offsetHeight / 2)
	})

	$effect(() => {
		if (!box) return
		const observer = new ResizeObserver(([entry]) => (height = entry.contentRect.height))
		observer.observe(box)
		return () => observer.disconnect()
	})
</script>

<div bind:this={box} class="overflow-hidden {className}">
	<div
		class="relative transition-transform duration-700 ease-out"
		style="transform: translateY({offset}px)"
	>
		{#each lines as item, i}
			<div bind:this={lineEls[i]}>{@render line(item, i)}</div>
		{/each}
	</div>
</div>
