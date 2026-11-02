<script lang="ts">
	import type { Snippet } from 'svelte'
	import { ChevronLeft, ChevronRight } from 'lucide-svelte'

	let {
		title,
		href,
		itemClass = 'w-40 md:w-44',
		children
	}: {
		title: string
		href?: string
		itemClass?: string
		children: Snippet<[string]>
	} = $props()

	let track = $state<HTMLDivElement>()

	function scrollBy(direction: 1 | -1) {
		track?.scrollBy({ left: direction * track.clientWidth * 0.8, behavior: 'smooth' })
	}
</script>

<section class="group/shelf">
	<div class="mb-3 flex items-end justify-between">
		<h2 class="text-xl font-bold tracking-tight">{title}</h2>
		<div class="flex items-center gap-1">
			{#if href}
				<a {href} class="mr-2 text-xs font-medium text-fg-muted hover:text-fg">查看全部</a>
			{/if}
			<button
				class="grid h-7 w-7 place-items-center rounded-full text-fg-muted hover:bg-line/5 hover:text-fg"
				onclick={() => scrollBy(-1)}
				aria-label="向左捲動"
			>
				<ChevronLeft class="h-4 w-4" />
			</button>
			<button
				class="grid h-7 w-7 place-items-center rounded-full text-fg-muted hover:bg-line/5 hover:text-fg"
				onclick={() => scrollBy(1)}
				aria-label="向右捲動"
			>
				<ChevronRight class="h-4 w-4" />
			</button>
		</div>
	</div>
	<div
		bind:this={track}
		class="-mx-1 no-scrollbar flex snap-x gap-4 overflow-x-auto scroll-smooth px-1 pb-2"
	>
		{@render children(`shrink-0 snap-start ${itemClass}`)}
	</div>
</section>
