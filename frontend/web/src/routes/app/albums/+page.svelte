<script lang="ts">
	import { Play } from 'lucide-svelte'
	import type { PageData } from './$types'
	import { goto } from '$app/navigation'
	import { getContext } from 'svelte'
	import type { MusicTrack } from '$lib/types'
	import Album from '$lib/image/album.svelte'
  import { APIUrl } from '$lib/api'

	export let data: PageData
	const { albums, error, status } = data
	const playMusic = getContext<(track: MusicTrack) => void>('playMusic')

	function getCoverArtUrl(coverArt: string) {
		return `${APIUrl}/file/image?image_id=${coverArt}&image_size=400`
	}

	function playAlbum(album: any) {
		if (album.tracks && album.tracks.length > 0) {
			playMusic(album.tracks[0])
		}
	}
</script>

<svelte:head>
	<title>專輯 - Lithium Player</title>
</svelte:head>

<div class="grid grid-cols-1 gap-5 p-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
	{#each albums as album}
		<div class="overflow-hidden rounded-lg bg-base-200 shadow-lg transition-shadow hover:shadow-xl">
			<div
				class="group relative cursor-pointer"
				role="button"
				tabindex="0"
				on:click={() => goto(`/app/albums/${album.id}`)}
				on:keydown={(e) => e.key === 'Enter' && goto(`/app/albums/${album.id}`)}
			>
				{#if album.cover_art}
					<img
						src={getCoverArtUrl(album.cover_art)}
						alt={album.title}
						class="aspect-square w-full object-cover"
					/>
				{:else}
					<Album class="aspect-square w-full object-cover" />
				{/if}
				<button
					class="btn btn-circle btn-primary absolute bottom-4 right-0 opacity-0 transition-opacity group-hover:opacity-100"
					on:click|stopPropagation={() => playAlbum(album)}
				>
					<Play />
				</button>
			</div>
			<div class="p-4">
				<button
					class="cursor-pointer truncate text-left text-lg font-semibold hover:text-primary"
					on:click={() => goto(`/app/albums/${album.id}`)}
					on:keydown={(e) => e.key === 'Enter' && goto(`/app/albums/${album.id}`)}
				>
					{album.title}
				</button>
				<p class="truncate text-sm text-gray-500">{album.album_artist}</p>
				<p class="truncate text-xs text-gray-400">{album.tracks?.length || 0} 首歌曲</p>
			</div>
		</div>
	{/each}
</div>
