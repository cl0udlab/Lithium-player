<script>
	import { slide } from 'svelte/transition';
	import { Music } from 'lucide-svelte';
	import { File } from 'lucide-svelte';
	import { FileVideo } from 'lucide-svelte';

	export let isExpanded = true;
	console.log(isExpanded);
</script>

{#if isExpanded}
	<aside
		transition:slide={{ duration: 100, axis: 'x' }}
		class="border-base-300 bg-neutral fixed left-0 top-0 z-40 h-screen w-64 border-r pt-20 transition-transform sm:translate-x-0"
		aria-label="Sidebar"
	>
		<div class="bg-neutral h-full overflow-y-auto px-3 pb-4">
			<div class="space-y-2 font-medium">
				<a href="/" class="text-base-content hover:bg-base-100 flex items-center rounded-lg p-2">
					<Music />
					<span class="ms-3">Music</span>
				</a>
				<a href="/" class="text-base-content hover:bg-base-100 flex items-center rounded-lg p-2">
					<FileVideo />
					<span class="ms-3">Video</span>
				</a>
				<a href="/" class="text-base-content hover:bg-base-100 flex items-center rounded-lg p-2">
					<File />
					<span class="ms-3">File</span>
				</a>
			</div>
		</div>
	</aside>
{:else}
	<aside
		transition:slide={{ duration: 200, axis: 'x' }}
		class="border-base-300 bg-neutral fixed left-0 top-0 z-40 h-screen w-16 border-r pt-20 transition-transform sm:translate-x-0"
		aria-label="Sidebar"
	>
		<div class="bg-neutral flex h-full flex-col items-center overflow-hidden px-3 pb-4">
			<div class="space-y-2 font-medium">
				<a href="/" class="text-base-content hover:bg-base-100 flex items-center rounded-lg p-2">
					<Music />
				</a>
				<a href="/" class="text-base-content hover:bg-base-100 flex items-center rounded-lg p-2">
					<FileVideo />
				</a>
				<a href="/" class="text-base-content hover:bg-base-100 flex items-center rounded-lg p-2">
					<File />
				</a>
			</div>
		</div>
	</aside>
{/if}
