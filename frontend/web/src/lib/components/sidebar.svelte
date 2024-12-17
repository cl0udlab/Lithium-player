<script>
	import { crossfade } from 'svelte/transition';
	import { Music } from 'lucide-svelte';
	import { File } from 'lucide-svelte';
	import { FileVideo } from 'lucide-svelte';
	import { House } from 'lucide-svelte';

	export let isExpanded = true;

	const [send, receive] = crossfade({
		duration: 160
	});
</script>

{#if isExpanded}
	<aside
		in:receive={{ key: 'sidebar' }}
		out:send={{ key: 'sidebar' }}
		class="border-base-300 bg-base-100 fixed left-0 top-0 z-40 h-screen w-64 border-r pt-20 transition-transform sm:translate-x-0"
		aria-label="Sidebar"
	>
		<div class="bg-base-100 h-full overflow-y-auto px-3 pb-4">
			<div class="space-y-2 font-medium">
				<a href="/" class="text-base-content hover:bg-base-100 flex items-center rounded-lg p-2">
					<House />
					<span class="ms-3">Overview</span>
				</a>
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
		in:receive={{ key: 'sidebar' }}
		out:send={{ key: 'sidebar' }}
		class="border-base-300 bg-base-100 fixed left-0 top-0 z-40 h-screen w-16 border-r pt-20 transition-transform sm:translate-x-0"
		aria-label="Sidebar"
	>
		<div class="bg-base-100 flex h-full flex-col items-center overflow-hidden px-3 pb-4">
			<div class="space-y-2 font-medium">
				<a href="/" class="text-base-content hover:bg-base-100 flex items-center rounded-lg p-2">
					<House />
				</a>
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
