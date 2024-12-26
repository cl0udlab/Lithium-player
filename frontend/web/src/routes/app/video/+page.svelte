<script lang="ts">
	import type { PageData } from './$types'
	import { getContext } from 'svelte'
	import type { Video } from '$lib/types'
	import { Play } from 'lucide-svelte'

	export let data
	const { videos, error, status } = data
	const playVideo = getContext<(video: Video) => void>('playVideo')

	function handlePlay(video: Video) {
		playVideo(video)
	}

	function getDuration(seconds: number) {
		const hours = Math.floor(seconds / 3600)
		const minutes = Math.floor((seconds % 3600) / 60)
		const remainingSeconds = Math.floor(seconds % 60)

		if (hours > 0) {
			return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
		}
		return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
	}
	function getCoverArtUrl(coverArt: string) {
		return `http://localhost:8000/file/image?image_id=${coverArt}&image_size=400`
	}
</script>

<svelte:head>
	<title>影片 - Lithium Player</title>
</svelte:head>

{#if error}
	<div class="flex flex-col items-center justify-center p-8 text-error">
		<h2 class="mb-4 text-2xl font-bold">載入失敗</h2>
		<p class="text-lg">{error}</p>
		{#if status === 500}
			<button type="button" class="btn btn-error mt-4" onclick={() => window.location.reload()}>
				重試
			</button>
		{/if}
	</div>
{:else}
	<div class="grid grid-cols-1 gap-5 p-4 md:grid-cols-2 lg:grid-cols-4">
		{#each videos as video}
			<div class="card bg-base-200 shadow-xl">
				<figure class="relative aspect-video w-full overflow-hidden">
					{#if video.thumbnail}
						<img
							src={getCoverArtUrl(video.thumbnail)}
							alt={video.title}
							class="h-full w-full object-cover"
						/>
					{:else}
						<div class="h-full w-full bg-base-300"></div>
					{/if}
					<button class="btn btn-circle btn-primary absolute" onclick={() => handlePlay(video)}>
						<Play size={24} />
					</button>
				</figure>
				<div class="card-body">
					<h2 class="card-title truncate">{video.title}</h2>
					{#if video.duration}
						<p class="text-sm opacity-75">{getDuration(video.duration)}</p>
					{/if}
					{#if video.description}
						<p class="line-clamp-2 text-sm opacity-75">{video.description}</p>
					{/if}
				</div>
			</div>
		{/each}
	</div>
{/if}
