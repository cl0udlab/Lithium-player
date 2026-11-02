<script lang="ts">
	import { CircleCheck, CircleAlert, Info, X } from 'lucide-svelte'
	import { toaster } from '$lib/stores/toast.svelte'

	const icons = { success: CircleCheck, error: CircleAlert, info: Info }
	const colors = { success: 'text-success', error: 'text-danger', info: 'text-accent' }
</script>

<div {...toaster.root} class="fixed bottom-28 right-4 z-[100] flex w-80 flex-col gap-2 overflow-visible">
	{#each toaster.toasts as t (t.id)}
		{@const Icon = icons[t.data.kind]}
		<div
			{...t.content}
			class="relative flex animate-slide-up gap-3 overflow-hidden rounded-xl border border-line/10 bg-surface-2 p-3.5 pr-9 shadow-lg"
		>
			<Icon class="mt-0.5 h-4 w-4 shrink-0 {colors[t.data.kind]}" />
			<div class="min-w-0">
				<p {...t.title} class="text-sm font-medium">{t.data.title}</p>
				{#if t.data.description}
					<p {...t.description} class="mt-0.5 break-words text-xs text-fg-muted">
						{t.data.description}
					</p>
				{/if}
			</div>
			<button
				{...t.close}
				class="absolute right-2 top-2 rounded-sm p-1 text-fg-subtle hover:text-fg"
				aria-label="關閉通知"
			>
				<X class="h-3.5 w-3.5" />
			</button>
			<div
				class="absolute bottom-0 left-0 h-0.5 bg-line/20"
				style="width: {100 - t.percentage}%"
			></div>
		</div>
	{/each}
</div>
