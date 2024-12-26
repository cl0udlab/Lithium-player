<script lang="ts">
	export let data
	import { getContext } from 'svelte'
	import type { MusicTrack } from '$lib/types'
	import { Play } from 'lucide-svelte'
	import CD from '$lib/image/cd.svelte'
	const { musics, error, status } = data
	const playMusic = getContext<(track: MusicTrack) => void>('playMusic')

	function handlePlay(track: MusicTrack) {
		playMusic(track)
	}

	function getCoverArtUrl(coverArt: string) {
		return `http://localhost:8000/file/image?image_id=${coverArt}&image_size=400`
	}
</script>

<svelte:head>
	<title>音樂 - Lithium Player</title>
</svelte:head>

{#if error}
	<div class="flex flex-col items-center justify-center p-8 text-error">
		<h2 class="mb-4 text-2xl font-bold">載入失敗</h2>
		<p class="text-lg">{error}</p>
		{#if status === 500}
			<button type="button" class="btn btn-error mt-4" onclick={() => window.location.reload()}
				>重試</button
			>
		{/if}
	</div>
{:else}
	<div class="grid grid-cols-1 gap-5 p-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
		{#each musics as music}
			<div
				class="overflow-hidden rounded-lg bg-base-200 shadow-lg transition-shadow hover:shadow-xl"
			>
				<div class="group relative">
					{#if music.cover_art}
						<img
							src={getCoverArtUrl(music.cover_art)}
							alt="{music.title} Cover"
							class="aspect-square w-full object-cover"
						/>
					{:else}
						<CD class="aspect-square w-full object-cover" />
					{/if}
					<button
						class="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100"
						onclick={() => handlePlay(music)}
					>
						<Play size={48} class="text-white" />
					</button>
				</div>
				<div class="p-4">
					<h3 class="truncate text-lg font-semibold">{music.title}</h3>
					<p class="truncate text-sm text-gray-500">{music.artist}</p>
					<p class="truncate text-xs text-gray-400">{music.album}</p>
				</div>
			</div>
		{/each}
	</div>
{/if}
