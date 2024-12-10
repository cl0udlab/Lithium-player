<script>
	import { AlignJustify } from 'lucide-svelte';
	import { Search } from 'lucide-svelte';
	import { ListChecks } from 'lucide-svelte';

	let { onToggle = () => {} } = $props();
	let expanded = $state(false);

	function handleToggle() {
		expanded = !expanded;
		onToggle(expanded);
	}
</script>

<nav class="border-base-300 fixed top-0 z-50 w-full border-b bg-white">
	<div class="navbar bg-base-100">
		<div class="navbar-start">
			<button type="button" class="btn btn-ghost btn-circle" onclick={handleToggle}>
				<AlignJustify />
			</button>
		</div>
		<div class="navbar-center">
			<label class="input input-bordered flex items-center gap-1">
				<input type="text" class="grow" placeholder="Search" />
				<Search />
			</label>
		</div>
		<div class="navbar-end">
			<button class="btn btn-ghost btn-circle">
				<div class="indicator">
					<ListChecks />
					<span class="badge badge-xs badge-primary indicator-item"></span>
				</div>
			</button>
		</div>
	</div>
</nav>
