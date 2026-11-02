<script lang="ts">
	import type { IconComponent } from '$lib/types'
	import { CircleAlert, Inbox } from 'lucide-svelte'
	import Button from './Button.svelte'

	let {
		kind = 'empty',
		title,
		message,
		icon,
		retry = false
	}: {
		kind?: 'empty' | 'error'
		title: string
		message?: string | null
		icon?: IconComponent
		retry?: boolean
	} = $props()

	const Icon = $derived(icon ?? (kind === 'error' ? CircleAlert : Inbox))
</script>

<div class="flex flex-col items-center justify-center px-6 py-20 text-center">
	<div
		class="mb-4 grid h-14 w-14 place-items-center rounded-2xl {kind === 'error'
			? 'bg-danger/10 text-danger'
			: 'bg-surface-2 text-fg-subtle'}"
	>
		<Icon class="h-6 w-6" />
	</div>
	<h2 class="text-lg font-semibold">{title}</h2>
	{#if message}
		<p class="mt-1 max-w-sm text-sm text-fg-muted">{message}</p>
	{/if}
	{#if retry}
		<Button class="mt-5" onclick={() => window.location.reload()}>重試</Button>
	{/if}
</div>
