<script lang="ts">
	import { playerliststat } from '$lib/stores/playerlist.js'
	import { onMount } from 'svelte'
	import { getContext } from 'svelte'
	import type { MusicTrack, Video } from '$lib/types'
	import { Play } from 'lucide-svelte'
	import CD from '$lib/image/cd.svelte'
	import Album from '$lib/image/album.svelte'
	import { goto } from '$app/navigation'
  import { APIUrl } from '$lib/api'
	export let data
	const { info, error, status } = data

	onMount(() => {
		playerliststat.initialize()
	})

	const playMusic = getContext<(track: MusicTrack) => void>('playMusic')
	const playVideo = getContext<(video: Video) => void>('playVideo')
	function handlePlay(track: MusicTrack) {
		playMusic(track)
	}

	function handlePlayVideo(video: Video) {
		playVideo(video)
	}
	function getCoverArtUrl(coverArt: string) {
		return `${APIUrl}/file/image?image_id=${coverArt}&image_size=400`
	}
</script>

<svelte:head>
	<title>首頁 - Lithium Player</title>
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
	<div class="flex flex-col gap-8 p-4">
		<section class="space-y-4">
			<h2 class="text-2xl font-bold text-primary">推薦專輯</h2>
			<div class="grid grid-cols-2 gap-4 overflow-hidden lg:grid-cols-3 xl:grid-cols-6">
				{#each info.Albums.sort(() => Math.random() - 0.5).slice(0, 10) as album}
					<div
						class="w-64 flex-shrink-0 rounded-lg bg-base-200 shadow-lg backdrop-blur-sm transition-all hover:scale-105"
						id={album.id}
					>
						<div class="group relative">
							{#if album.cover_art}
								<img
									src={getCoverArtUrl(album.cover_art)}
									alt="{album.title} Cover"
									class="aspect-square w-full rounded-t-lg object-cover"
								/>
							{:else}
								<Album class="aspect-square w-full rounded-t-lg bg-base-300" />
							{/if}
							<button
								class="absolute inset-0 flex items-center justify-center bg-primary/30 opacity-0 backdrop-blur-sm transition-all group-hover:opacity-100"
								onclick={() => goto(`/app/albums/${album.id}`)}
								onkeydown={(e) => e.key === 'Enter' && goto(`/app/albums/${album.id}`)}
							>
								<Play class="text-base-100" size={48} />
							</button>
						</div>
						<div class="p-4">
							<h3 class="truncate text-lg font-bold">{album.title}</h3>
							<p class="truncate text-sm opacity-75">{album.artist}</p>
							<p class="mt-1 text-xs opacity-60">{album.total_tracks || 0} 首歌曲</p>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- 最新加入 -->
		<section class="space-y-4">
			<h2 class="text-2xl font-bold text-primary">最新加入</h2>
			<div class="grid grid-cols-2 gap-4 lg:grid-cols-4 xl:grid-cols-6">
				{#each info.Musics.slice(0, 12) as music}
					<div
						class="rounded-lg bg-base-200 shadow-lg backdrop-blur-sm transition-all hover:scale-105"
						id={music.id}
					>
						<div class="group relative">
							{#if music.cover_art}
								<img
									src={getCoverArtUrl(music.cover_art)}
									alt="{music.title} Cover"
									class="aspect-square w-full rounded-t-lg object-cover"
								/>
							{:else}
								<CD class="aspect-square w-full rounded-t-lg bg-base-300" />
							{/if}
							<button
								class="absolute inset-0 flex items-center justify-center bg-primary/30 opacity-0 backdrop-blur-sm transition-all group-hover:opacity-100"
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
			<h2 class="text-2xl font-bold text-primary">影片清單</h2>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
				{#each info.Videos || [] as video}
					<div
						class="overflow-hidden rounded-lg bg-base-200 shadow-lg backdrop-blur-sm transition-all hover:scale-105"
						id={video.id}
					>
						<div class="group relative">
							{#if video.thumbnail}
								<img
									src={getCoverArtUrl(video.thumbnail)}
									alt="{video.title} Cover"
									class="aspect-video w-full object-cover"
								/>
							{:else}
								<div class="aspect-video w-full bg-base-300"></div>
							{/if}
							<button
								class="absolute inset-0 flex items-center justify-center bg-primary/30 opacity-0 backdrop-blur-sm transition-all group-hover:opacity-100"
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
