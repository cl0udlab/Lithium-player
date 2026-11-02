<script lang="ts" generics="T extends string">
	import type { IconComponent } from '$lib/types'
	import type { Snippet } from 'svelte'
	import { Tabs } from 'melt/builders'

	let {
		value = $bindable(),
		items,
		content,
		class: className = ''
	}: {
		value: T
		items: { value: T; label: string; icon?: IconComponent }[]
		content: Snippet<[T]>
		class?: string
	} = $props()

	const tabs = new Tabs<T>({
		value: () => value,
		onValueChange: (v) => (value = v)
	})
</script>

<div class={className}>
	<div {...tabs.triggerList} class="flex gap-1 rounded-lg bg-surface-2 p-1">
		{#each items as item (item.value)}
			<button
				{...tabs.getTrigger(item.value)}
				class="flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-fg-muted transition-colors hover:text-fg data-[active]:bg-surface-3 data-[active]:text-fg data-[active]:shadow-sm"
			>
				{#if item.icon}
					<item.icon class="h-4 w-4" />
				{/if}
				{item.label}
			</button>
		{/each}
	</div>
	{#each items as item (item.value)}
		<div {...tabs.getContent(item.value)} class="mt-4">
			{#if tabs.value === item.value}
				{@render content(item.value)}
			{/if}
		</div>
	{/each}
</div>
