<script lang="ts">
	import type { Snippet } from 'svelte'
	import { Dialog } from 'melt/builders'
	import { X } from 'lucide-svelte'

	let {
		open = $bindable(false),
		title,
		description,
		class: className = 'w-[min(32rem,calc(100vw-2rem))]',
		children,
		footer
	}: {
		open?: boolean
		title?: string
		description?: string
		class?: string
		children: Snippet
		footer?: Snippet
	} = $props()

	const dialog = new Dialog({ onOpenChange: (value) => (open = value) })

	$effect(() => {
		if (open !== dialog.open) dialog.open = open
	})
</script>

<dialog
	{...dialog.content}
	class="group overflow-visible opacity-0 transition-opacity duration-150 data-[open]:opacity-100"
>
	<div class="fixed inset-0 bg-black/60 backdrop-blur-xs" aria-hidden="true"></div>
	<div
		class="relative flex max-h-[calc(100vh-4rem)] scale-95 flex-col overflow-hidden rounded-2xl border border-line/10 bg-surface shadow-2xl transition-transform duration-150 group-data-[open]:scale-100 {className}"
	>
		{#if title}
			<div class="flex items-start justify-between gap-4 px-6 pt-5 pb-2">
				<div>
					<h2 class="text-lg font-semibold">{title}</h2>
					{#if description}
						<p class="mt-1 text-sm text-fg-muted">{description}</p>
					{/if}
				</div>
				<button
					class="-mr-2 rounded-full p-1.5 text-fg-subtle transition-colors hover:bg-line/5 hover:text-fg"
					onclick={() => (open = false)}
					aria-label="關閉"
				>
					<X class="h-4 w-4" />
				</button>
			</div>
		{/if}
		<div class="min-h-0 flex-1 overflow-y-auto px-6 py-4">
			{@render children()}
		</div>
		{#if footer}
			<div class="flex justify-end gap-2 border-t border-line/5 bg-surface-2/40 px-6 py-3">
				{@render footer()}
			</div>
		{/if}
	</div>
</dialog>
