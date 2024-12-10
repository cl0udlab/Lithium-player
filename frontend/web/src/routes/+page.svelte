<script lang="ts">
	import Navbar from '$lib/components/navbar.svelte';
	import Sidebar from '$lib/components/sidebar.svelte';
	let isExpanded = $state(true);

	function handleToggle(expanded: boolean) {
		isExpanded = expanded;
	}
</script>

<Navbar onToggle={handleToggle} />
<Sidebar {isExpanded} />
