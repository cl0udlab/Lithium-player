<script lang="ts" module>
	import type { IconComponent } from '$lib/types'

	export interface ActionItem {
		label: string
		icon?: IconComponent
		danger?: boolean
		onselect: () => void
	}
</script>

<script lang="ts">
	import { Popover } from 'melt/builders'
	import { EllipsisVertical } from 'lucide-svelte'

	let {
		items,
		label = '更多操作',
		class: className = ''
	}: {
		items: ActionItem[]
		label?: string
		class?: string
	} = $props()

	const popover = new Popover({
		floatingConfig: { computePosition: { placement: 'bottom-end' }, offset: { mainAxis: 4 } }
	})

	function select(item: ActionItem) {
		popover.open = false
		item.onselect()
	}
</script>

<button
	{...popover.trigger}
	class="grid h-8 w-8 place-items-center rounded-full bg-black/55 text-white backdrop-blur-sm transition-colors hover:bg-black/75 {className}"
	aria-label={label}
>
	<EllipsisVertical class="h-4 w-4" />
</button>

<div
	{...popover.content}
	class="w-48 rounded-xl border border-line/10 bg-surface-2 p-1.5 shadow-lg"
>
	{#each items as item (item.label)}
		<button
			onclick={() => select(item)}
			class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm {item.danger
				? 'text-danger hover:bg-danger/10'
				: 'text-fg-muted hover:bg-line/5 hover:text-fg'}"
		>
			{#if item.icon}
				<item.icon class="h-4 w-4 shrink-0" />
			{/if}
			{item.label}
		</button>
	{/each}
</div>
