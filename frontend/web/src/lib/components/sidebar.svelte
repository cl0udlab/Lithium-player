<script>
	import { crossfade } from 'svelte/transition'
	import { Music } from 'lucide-svelte'
	import { File } from 'lucide-svelte'
	import { FileVideo } from 'lucide-svelte'
	import { House } from 'lucide-svelte'
	import { Settings2 } from 'lucide-svelte'

	export let isExpanded = true

	const [send, receive] = crossfade({
		duration: 160
	})
</script>

{#if isExpanded}
	<aside
		in:receive={{ key: 'sidebar' }}
		out:send={{ key: 'sidebar' }}
		class="fixed left-0 top-0 z-40 h-screen w-64 border-r border-base-300 bg-base-100 pt-20 transition-transform sm:translate-x-0"
		aria-label="Sidebar"
	>
		<div class="flex h-full flex-col justify-between overflow-y-auto bg-base-100 px-3 pb-4">
			<div class="flex flex-col space-y-2 font-medium">
				<a href="/app" class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100">
					<House />
					<span class="ms-3">Overview</span>
				</a>
				<div class="collapse collapse-arrow">
					<input type="checkbox" />
					<div
						class="collapse-title flex min-h-0 items-center rounded-lg px-2 py-1.5 hover:bg-base-100"
					>
						<Music />
						<span class="ms-3">Music</span>
					</div>
					<div class="collapse-content px-0 py-0">
						<ul class="space-y-0.5 ps-4">
							<li>
								<a
									href="/app/music"
									class="flex items-center rounded-lg px-2 py-1.5 hover:bg-base-100"
								>
									<span class="ms-3">音樂</span>
								</a>
							</li>
							<li>
								<a
									href="/app/albums"
									class="flex items-center rounded-lg px-2 py-1.5 hover:bg-base-100"
								>
									<span class="ms-3">專輯</span>
								</a>
							</li>
							<li>
								<a
									href="/app/playlist"
									class="flex items-center rounded-lg px-2 py-1.5 hover:bg-base-100"
								>
									<span class="ms-3">撥放清單</span>
								</a>
							</li>
						</ul>
					</div>
				</div>
				<a
					href="/app/video"
					class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100"
				>
					<FileVideo />
					<span class="ms-3">Video</span>
				</a>
				<a
					href="/app/file"
					class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100"
				>
					<File />
					<span class="ms-3">File</span>
				</a>
			</div>
			<div class="mt-auto pt-4">
				<a
					href="/app/setting"
					class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100"
				>
					<Settings2 />
					<span class="ms-3">設定</span>
				</a>
			</div>
		</div>
	</aside>
{:else}
	<aside
		in:receive={{ key: 'sidebar' }}
		out:send={{ key: 'sidebar' }}
		class="fixed left-0 top-0 z-40 h-screen w-16 border-r border-base-300 bg-base-100 pt-20 transition-transform sm:translate-x-0"
		aria-label="Sidebar"
	>
		<div class="flex h-full flex-col items-center overflow-hidden bg-base-100 px-3 pb-4">
			<div class="space-y-2 font-medium">
				<a href="/app" class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100">
					<House />
				</a>
				<a
					href="/app/albums"
					class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100"
				>
					<Music />
				</a>
				<a
					href="/app/video"
					class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100"
				>
					<FileVideo />
				</a>
				<a
					href="/app/file"
					class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100"
				>
					<File />
				</a>
			</div>
			<div class="mt-auto pt-4">
				<a
					href="/app/setting"
					class="flex items-center rounded-lg p-2 text-base-content hover:bg-base-100"
				>
					<Settings2 />
				</a>
			</div>
		</div>
	</aside>
{/if}
