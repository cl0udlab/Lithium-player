<script lang="ts">
	import { page } from '$app/state'
	import Button from '$lib/components/ui/Button.svelte'
</script>

<div class="grid min-h-screen place-content-center px-4 text-center">
	<p class="text-7xl font-black tracking-tight text-accent">{page.status}</p>
	<p class="mt-3 text-fg-muted">{page.error?.message}</p>
	<Button class="mx-auto mt-6" href="/app">回到首頁</Button>
</div>
