<script lang="ts">
	import { playerliststat } from '$lib/stores/playerlist.js';
	import { onMount } from 'svelte';
	import { getContext } from 'svelte';
	import type { MusicTrack } from '$lib/types';
	import { Play } from 'lucide-svelte';
	import CD from '$lib/image/cd.svelte';
	export let data;
	const { musics, error, status } = data;

	onMount(() => {
		playerliststat.initialize();
	});

	const playMusic = getContext<(track: MusicTrack) => void>('playMusic');

	function handlePlay(track: MusicTrack) {
		playMusic(track);
	}

	function getCoverArtUrl(coverArt: string) {
		return `http://localhost:8000/file/image?image_id=${coverArt}&image_size=400`;
	}
</script>

{#if error}
	<div class="text-error flex flex-col items-center justify-center p-8">
		<h2 class="mb-4 text-2xl font-bold">載入失敗</h2>
		<p class="text-lg">{error}</p>
		{#if status === 500}
			<button type="button" class="btn btn-error mt-4" onclick={() => window.location.reload()}
				>重試</button
			>
		{/if}
	</div>
{:else}
	<div class="grid grid-cols-1 gap-5 p-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
		{#each musics as music}
			<div
				class="bg-base-200 overflow-hidden rounded-lg shadow-lg transition-shadow hover:shadow-xl"
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
