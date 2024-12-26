<script>
	import { AlignJustify } from 'lucide-svelte'
	import { Search } from 'lucide-svelte'
	import { ListChecks } from 'lucide-svelte'

	let { onToggle = () => {} } = $props()
	let expanded = $state(false)

	function handleToggle() {
		expanded = !expanded
		onToggle(expanded)
	}
</script>

<nav class="fixed top-0 z-50 w-full border-b border-base-300 bg-white">
	<div class="navbar bg-base-100">
		<div class="navbar-start">
			<button type="button" class="btn btn-circle btn-ghost" onclick={handleToggle}>
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
			<button class="btn btn-circle btn-ghost">
				<div class="indicator">
					<ListChecks />
					<span class="badge indicator-item badge-primary badge-xs"></span>
				</div>
			</button>
		</div>
	</div>
</nav>
