<script lang="ts">
	import { page } from '$app/stores'
</script>

<div class="grid h-screen place-content-center bg-white px-4">
	<h1 class="uppercase tracking-widest text-gray-500">{$page.status} | {$page.error?.message}</h1>
	<button class="btn mt-4" on:click={() => (location.href = '/')}>Back to Home</button>
</div>
