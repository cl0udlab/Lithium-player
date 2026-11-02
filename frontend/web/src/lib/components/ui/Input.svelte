<script lang="ts">
	import type { IconComponent } from '$lib/types'
	import type { HTMLInputAttributes } from 'svelte/elements'

	let {
		value = $bindable(),
		icon: Icon,
		class: className = '',
		ref = $bindable(),
		...rest
	}: HTMLInputAttributes & {
		icon?: IconComponent
		ref?: HTMLInputElement
	} = $props()
</script>

<div class="relative {className}">
	{#if Icon}
		<Icon class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-fg-subtle" />
	{/if}
	<input
		bind:this={ref}
		bind:value
		class="h-10 w-full rounded-lg border border-line/10 bg-surface-2 text-sm text-fg outline-hidden transition-colors placeholder:text-fg-subtle hover:border-line/20 focus:border-accent/60 focus:ring-2 focus:ring-accent/20 disabled:opacity-50 {Icon
			? 'pl-9 pr-3'
			: 'px-3'}"
		{...rest}
	/>
</div>
