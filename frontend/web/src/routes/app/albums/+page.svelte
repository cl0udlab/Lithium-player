<script lang="ts">
	import LibraryToolbar from '$lib/components/ui/LibraryToolbar.svelte'
	import { getContext } from 'svelte'
	import { coverUrl } from '$lib/api'
	import { fetchAlbumTracks } from '$lib/utils/library'
	import type { PlayableTrack } from '$lib/types'
	import MediaCard from '$lib/components/ui/MediaCard.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playMusiclist =
		getContext<(tracks: PlayableTrack[], startIndex?: number) => void>('playMusiclist')
	const albums: any[] = $derived(data.albums ?? [])

	async function playAlbum(albumId: number) {
		const tracks = await fetchAlbumTracks(albumId)
		if (tracks.length) playMusiclist(tracks)
	}
</script>

<svelte:head>
	<title>專輯 - Lithium Player</title>
</svelte:head>

{#if data.error}
	<StatusMessage kind="error" title="載入失敗" message={data.error} retry={data.status === 500} />
{:else}
	<PageHeader title="專輯" subtitle="{data.total} 張" />
	<LibraryToolbar
		path="/app/albums"
		total={data.total}
		page={data.page}
		size={data.size}
		q={data.q}
	/>
	{#if albums.length}
		<div class="grid grid-cols-2 gap-x-5 gap-y-7 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6">
			{#each albums as album (album.id)}
				<MediaCard
					title={album.title}
					subtitle={album.album_artist}
					meta="{album.tracks?.length ?? album.total_tracks ?? 0} 首"
					cover={coverUrl(album.cover_art, 400)}
					href="/app/albums/{album.id}"
					onplay={() => playAlbum(album.id)}
				/>
			{/each}
		</div>
	{:else}
		<StatusMessage
			title="還沒有專輯"
			message="可到設定頁掃描資料夾或同步 Subsonic，亦可調整搜尋條件。"
		/>
	{/if}
{/if}
