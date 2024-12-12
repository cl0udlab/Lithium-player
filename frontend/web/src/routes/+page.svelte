<script lang="ts">
	import Navbar from '$lib/components/navbar.svelte';
	import Sidebar from '$lib/components/sidebar.svelte';
	import { stars } from '$lib/init/store';
	import { onMount } from 'svelte';

	let isExpanded = $state(true);

	onMount(() => {
		stars.initialize();
	});

	function handleToggle(expanded: boolean) {
		isExpanded = expanded;
	}
</script>

<Navbar onToggle={handleToggle} />
<Sidebar {isExpanded} />
