<script lang="ts">
	import Button from './Button.svelte'
	import Dialog from './Dialog.svelte'

	let {
		open = $bindable(false),
		title,
		message,
		confirmLabel = '確定',
		onconfirm
	}: {
		open?: boolean
		title: string
		message?: string
		confirmLabel?: string
		onconfirm: () => Promise<void> | void
	} = $props()

	let busy = $state(false)

	async function confirm() {
		busy = true
		try {
			await onconfirm()
			open = false
		} finally {
			busy = false
		}
	}
</script>

<Dialog bind:open {title}>
	{#if message}
		<p class="text-sm text-fg-muted">{message}</p>
	{/if}
	{#snippet footer()}
		<Button variant="ghost" onclick={() => (open = false)}>取消</Button>
		<Button variant="danger" disabled={busy} onclick={confirm}>{confirmLabel}</Button>
	{/snippet}
</Dialog>
