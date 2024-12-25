<script lang="ts">
	import { playerliststat } from '$lib/stores/playerlist.js';
	import { onMount } from 'svelte';
	import { getContext } from 'svelte';
	import type { MusicTrack, Video } from '$lib/types';
	import { Play } from 'lucide-svelte';
	import CD from '$lib/image/cd.svelte';
  import Album from '$lib/image/album.svelte';
	import { goto } from '$app/navigation';
	export let data;
	const { info, error, status } = data;

	onMount(() => {
		playerliststat.initialize();
	});

	const playMusic = getContext<(track: MusicTrack) => void>('playMusic');
	const playVideo = getContext<(video: Video) => void>('playVideo');
	function handlePlay(track: MusicTrack) {
		playMusic(track);
	}

	function handlePlayVideo(video: Video) {
		playVideo(video);
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
	<div class="flex flex-col gap-8 p-4">
		<section class="space-y-4">
			<h2 class="text-primary text-2xl font-bold">推薦專輯</h2>
			<div class="overflow-x-auto">
				<div class="grid grid-cols-2 gap-4 overflow-hidden lg:grid-cols-4 xl:grid-cols-6">
					{#each info.Albums.sort(() => Math.random() - 0.5).slice(0, 10) as album}
						<div
							class="bg-base-200 w-64 flex-shrink-0 rounded-lg shadow-lg backdrop-blur-sm transition-all hover:scale-105"
						>
							<div class="group relative">
								{#if album.cover_art}
									<img
										src={getCoverArtUrl(album.cover_art)}
										alt="{album.title} Cover"
										class="aspect-square w-full rounded-t-lg object-cover"
									/>
								{:else}
									<Album class="bg-base-300 aspect-square w-full rounded-t-lg" />
								{/if}
								<button
									class="bg-primary/30 absolute inset-0 flex items-center justify-center opacity-0 backdrop-blur-sm transition-all group-hover:opacity-100"
									onclick={() => goto(`/app/albums/${album.id}`)}
									onkeydown={(e) => e.key === 'Enter' && goto(`/app/albums/${album.id}`)}
								>
									<Play class="text-base-100" size={48} />
								</button>
							</div>
							<div class="p-4">
								<h3 class="truncate text-lg font-bold">{album.title}</h3>
								<p class="truncate text-sm opacity-75">{album.artist}</p>
								<p class="mt-1 text-xs opacity-60">{album.tracks?.length || 0} 首歌曲</p>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</section>

		<!-- 最新加入 -->
		<section class="space-y-4">
			<h2 class="text-primary text-2xl font-bold">最新加入</h2>
			<div class="grid grid-cols-2 gap-4 lg:grid-cols-4 xl:grid-cols-6">
				{#each info.Musics.slice(0, 12) as music}
					<div
						class="bg-base-200 rounded-lg shadow-lg backdrop-blur-sm transition-all hover:scale-105"
					>
						<div class="group relative">
							{#if music.cover_art}
								<img
									src={getCoverArtUrl(music.cover_art)}
									alt="{music.title} Cover"
									class="aspect-square w-full rounded-t-lg object-cover"
								/>
							{:else}
								<CD class="bg-base-300 aspect-square w-full rounded-t-lg" />
							{/if}
							<button
								class="bg-primary/30 absolute inset-0 flex items-center justify-center opacity-0 backdrop-blur-sm transition-all group-hover:opacity-100"
								onclick={() => handlePlay(music)}
							>
								<Play class="text-base-100" size={36} />
							</button>
						</div>
						<div class="p-3">
							<h3 class="truncate text-sm font-bold">{music.title}</h3>
							<p class="truncate text-xs opacity-75">{music.artist}</p>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<section class="space-y-4">
			<h2 class="text-primary text-2xl font-bold">影片清單</h2>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				{#each info.Videos || [] as video}
					<div
						class="bg-base-200 overflow-hidden rounded-lg shadow-lg backdrop-blur-sm transition-all hover:scale-105"
					>
						<div class="group relative">
							{#if video.thumbnail}
								<img
									src={getCoverArtUrl(video.thumbnail)}
									alt="{video.title} Cover"
									class="aspect-video w-full object-cover"
								/>
							{:else}
								<div class="bg-base-300 aspect-video w-full"></div>
							{/if}
							<button
								class="bg-primary/30 absolute inset-0 flex items-center justify-center opacity-0 backdrop-blur-sm transition-all group-hover:opacity-100"
								onclick={() => handlePlayVideo(video)}
							>
								<Play class="text-base-100" size={48} />
							</button>
						</div>
						<div class="p-4">
							<h3 class="truncate text-lg font-bold">{video.title}</h3>
						</div>
					</div>
				{/each}
			</div>
		</section>
	</div>
{/if}
