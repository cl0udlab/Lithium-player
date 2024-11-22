<script>
	let count = 0

	function Click() {
		count += 1
	}
</script>

<img src="/svelte.electron.png" width="200" alt="Svelte logo" />
<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://kit.svelte.dev">kit.svelte.dev</a> to read the documentation</p>
<button on:click={Click}>
	Click me {count} times
</button>

<a href="/testpage">go to other page</a>
