<script lang="ts">
	import type { Snippet } from 'svelte'
	import type { IconComponent } from '$lib/types'
	import { Play, Disc3 } from 'lucide-svelte'

	let {
		title,
		subtitle,
		meta,
		cover,
		shape = 'square',
		href,
		onplay,
		badge,
		placeholder: Placeholder = Disc3,
		actions,
		class: className = ''
	}: {
		title: string
		subtitle?: string | null
		meta?: string | null
		cover?: string | null
		shape?: 'square' | 'video' | 'portrait'
		href?: string
		onplay?: () => void
		badge?: string
		placeholder?: IconComponent
		/** 右上角的操作選單, 滑鼠移上去才顯示 */
		actions?: Snippet
		class?: string
	} = $props()

	const aspect = { square: 'aspect-square', video: 'aspect-video', portrait: 'aspect-[3/4]' }
	const tag = $derived(href ? 'a' : 'button')

	function onclick() {
		if (!href) onplay?.()
	}
</script>

<div class="group min-w-0 {className}">
	<div class="relative overflow-hidden rounded-xl bg-surface-2 {aspect[shape]}">
		<svelte:element
			this={tag}
			{href}
			type={href ? undefined : 'button'}
			{onclick}
			class="block h-full w-full"
			aria-label={title}
		>
			{#if cover}
				<img
					src={cover}
					alt=""
					loading="lazy"
					referrerpolicy="no-referrer"
					class="h-full w-full object-cover"
				/>
			{:else}
				<div class="grid h-full w-full place-items-center bg-surface-3">
					<Placeholder class="h-1/3 w-1/3 text-fg-subtle" />
				</div>
			{/if}
			<div class="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/25"></div>
		</svelte:element>
		{#if badge}
			<span
				class="pointer-events-none absolute top-2 left-2 rounded-md bg-black/60 px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-white uppercase backdrop-blur-sm"
			>
				{badge}
			</span>
		{/if}
		{#if actions}
			<div
				class="absolute top-2 right-2 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100 has-[[aria-expanded=true]]:opacity-100"
			>
				{@render actions()}
			</div>
		{/if}
		{#if onplay}
			<button
				class="absolute right-2 bottom-2 grid h-11 w-11 translate-y-2 place-items-center rounded-full bg-accent text-accent-fg opacity-0 shadow-md transition-all group-hover:translate-y-0 group-hover:opacity-100 hover:bg-accent-hover focus-visible:translate-y-0 focus-visible:opacity-100"
				onclick={onplay}
				aria-label="播放 {title}"
			>
				<Play class="ml-0.5 h-5 w-5" fill="currentColor" />
			</button>
		{/if}
	</div>
	<svelte:element
		this={tag}
		{href}
		type={href ? undefined : 'button'}
		{onclick}
		tabindex={-1}
		class="mt-2.5 block w-full px-0.5 text-left"
	>
		<p class="truncate text-sm font-semibold">{title}</p>
		{#if subtitle}
			<p class="truncate text-xs text-fg-muted">{subtitle}</p>
		{/if}
		{#if meta}
			<p class="mt-0.5 truncate text-[11px] text-fg-subtle">{meta}</p>
		{/if}
	</svelte:element>
</div>
