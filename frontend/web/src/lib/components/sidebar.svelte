<script>
	import { Music } from 'lucide-svelte';
	import { File } from 'lucide-svelte';
	import { FileVideo } from 'lucide-svelte';
</script>

<aside
	id="logo-sidebar"
	class="fixed left-0 top-0 z-40 h-screen w-64 -translate-x-full border-r border-gray-200 bg-white pt-20 transition-transform sm:translate-x-0 dark:border-gray-700 dark:bg-gray-800"
	aria-label="Sidebar"
>
	<div class="h-full overflow-y-auto bg-white px-3 pb-4 dark:bg-gray-800">
		<ul class="space-y-2 font-medium">
			<li>
				<a
					href="/"
					class="group flex items-center rounded-lg p-2 text-gray-900 hover:bg-gray-100 dark:text-white dark:hover:bg-gray-700"
				>
					<Music />
					<span class="ms-3">Music</span>
				</a>
			</li>
			<li>
				<a
					href="/"
					class="group flex items-center rounded-lg p-2 text-gray-900 hover:bg-gray-100 dark:text-white dark:hover:bg-gray-700"
				>
					<FileVideo />
					<span class="ms-3">Video</span>
				</a>
			</li>
			<li>
				<a
					href="/"
					class="group flex items-center rounded-lg p-2 text-gray-900 hover:bg-gray-100 dark:text-white dark:hover:bg-gray-700"
				>
					<File />
					<span class="ms-3">File</span>
				</a>
			</li>
		</ul>
	</div>
</aside>
