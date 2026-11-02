<script lang="ts">
	import { getContext } from 'svelte'
	import { Play, Shuffle, Disc3 } from 'lucide-svelte'
	import { coverUrl } from '$lib/api'
	import { formatDuration } from '$lib/utils/library'
	import type { MusicTrack, PlayableTrack } from '$lib/types'
	import Button from '$lib/components/ui/Button.svelte'
	import TrackList from '$lib/components/ui/TrackList.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playMusiclist = getContext<(tracks: PlayableTrack[], startIndex?: number) => void>(
		'playMusiclist'
	)
	const album = $derived(data.album)
	const tracks: PlayableTrack[] = $derived(
		((album.tracks ?? []) as any[])
			.map((t): MusicTrack => ({ ...t, kind: 'music' }))
			.sort(
				(a: any, b: any) =>
					(a.disc_number ?? 0) - (b.disc_number ?? 0) ||
					(a.track_number ?? 0) - (b.track_number ?? 0)
			)
	)
	const totalSeconds = $derived(tracks.reduce((sum, t: any) => sum + (t.duration ?? 0), 0))
	const cover = $derived(coverUrl(album.cover_art, 600))
</script>

<svelte:head>
	<title>{album.title} - Lithium Player</title>
</svelte:head>

<section class="mb-8 pt-4">
	<div class="relative flex flex-col gap-6 sm:flex-row sm:items-end">
		<div
			class="aspect-square w-44 shrink-0 overflow-hidden rounded-2xl bg-surface-3 md:w-56"
		>
			{#if cover}
				<img src={cover} alt={album.title} class="h-full w-full object-cover" />
			{:else}
				<Disc3 class="m-auto h-full w-1/3 text-fg-subtle" />
			{/if}
		</div>
		<div class="min-w-0">
			<p class="text-sm text-fg-muted">專輯</p>
			<h1 class="mt-2 text-4xl font-black tracking-tight md:text-6xl">{album.title}</h1>
			<p class="mt-3 text-sm text-fg-muted">
				<span class="font-semibold text-fg">{album.album_artist}</span>
				{#if album.release_date}· {album.release_date}{/if}
				{#if album.genre}· {album.genre}{/if}
				· {tracks.length} 首 · {formatDuration(totalSeconds)}
			</p>
			<div class="mt-5 flex gap-2">
				<Button
					variant="primary"
					size="lg"
					onclick={() => playMusiclist(tracks)}
					disabled={!tracks.length}
				>
					<Play class="h-4 w-4" fill="currentColor" /> 播放
				</Button>
				<Button
					size="lg"
					onclick={() => playMusiclist([...tracks].sort(() => Math.random() - 0.5))}
					disabled={!tracks.length}
				>
					<Shuffle class="h-4 w-4" /> 隨機
				</Button>
			</div>
		</div>
	</div>
</section>

<TrackList {tracks} showCover={false} showAlbum={false} onplay={(i) => playMusiclist(tracks, i)} />
