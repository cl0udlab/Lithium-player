<script lang="ts">
	import { Play } from 'lucide-svelte'
	import type { PageData } from './$types'
	import { getContext } from 'svelte'
	import type { MusicTrack } from '$lib/types'
	import Album from '$lib/image/album.svelte'

	export let data: PageData
	const { album } = data
	const playMusic = getContext<(track: MusicTrack) => void>('playMusic')
	const playMusiclist = getContext<(track: MusicTrack) => void>('playMusiclist')

	function getCoverArtUrl(coverArt: string) {
		return `http://localhost:8000/file/image?image_id=${coverArt}&image_size=400`
	}

	function formatDuration(seconds: number) {
		const minutes = Math.floor(seconds / 60)
		const remainingSeconds = seconds % 60
		return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
	}

	function playAlbum() {
		playMusiclist(album.tracks)
	}
</script>

<svelte:head>
	<title>{album.title} - Lithium Player</title>
</svelte:head>

<div class="p-6">
	<div class="flex gap-8">
		{#if album.cover_art}
			<img
				src={getCoverArtUrl(album.cover_art)}
				alt={album.title}
				class="h-64 w-64 rounded-lg object-cover shadow-xl"
			/>
		{:else}
			<Album class="h-64 w-64 rounded-lg object-cover shadow-xl" />
		{/if}
		<div class="flex flex-col justify-between py-4">
			<div>
				<h1 class="mb-2 text-4xl font-bold">{album.title}</h1>
				<p class="mb-4 text-xl opacity-75">{album.album_artist}</p>
				<p class="text-sm opacity-75">{album.genre || '未知類型'} • {album.tracks.length} 首歌曲</p>
			</div>
			<button class="btn btn-primary w-fit" on:click={playAlbum}>
				<Play />
				播放全部
			</button>
		</div>
	</div>

	<div class="mt-8">
		<table class="table">
			<tbody>
				{#each album.tracks as track, i}
					<tr class="hover">
						<td class="w-12">{i + 1}</td>
						<td class="w-12">
							<button class="btn btn-circle btn-ghost btn-sm" on:click={() => playMusic(track)}>
								<Play size={16} />
							</button>
						</td>
						<td>
							<p class="font-medium">{track.title}</p>
							<p class="text-sm opacity-75">{track.artist}</p>
						</td>
						<td class="text-right">
							<span class="opacity-75">{formatDuration(track.duration)}</span>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
