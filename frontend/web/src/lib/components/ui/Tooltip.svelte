<script lang="ts">
	import type { Snippet } from 'svelte'
	import { Tooltip } from 'melt/builders'

	let {
		text,
		placement = 'right',
		disabled = false,
		children
	}: {
		text: string
		placement?: 'top' | 'right' | 'bottom' | 'left'
		disabled?: boolean
		children: Snippet<[Record<string, unknown>]>
	} = $props()

	const tooltip = new Tooltip({
		openDelay: 300,
		floatingConfig: () => ({ computePosition: { placement }, offset: { mainAxis: 8 } })
	})
</script>

{@render children(disabled ? {} : tooltip.trigger)}

{#if !disabled}
	<div
		{...tooltip.content}
		class="rounded-md border border-line/10 bg-surface-3 px-2.5 py-1 text-xs font-medium text-fg shadow-xl"
	>
		{text}
	</div>
{/if}
