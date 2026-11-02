<script lang="ts">
	import { getContext, onMount } from 'svelte'
	import { Play, Disc3, Music, Clapperboard, ListMusic, FolderSearch } from 'lucide-svelte'
	import { apiFetch, coverUrl } from '$lib/api'
	import { playerliststat } from '$lib/stores/playerlist'
	import { fetchAlbumTracks, platformLabel } from '$lib/utils/library'
	import type { MusicTrack, PlayableTrack, StreamTrack, Video } from '$lib/types'
	import Button from '$lib/components/ui/Button.svelte'
	import MediaCard from '$lib/components/ui/MediaCard.svelte'
	import Shelf from '$lib/components/ui/Shelf.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playMusic = getContext<(track: PlayableTrack) => void>('playMusic')
	const playMusiclist = getContext<(tracks: PlayableTrack[], startIndex?: number) => void>(
		'playMusiclist'
	)
	const playVideo = getContext<(video: Video) => void>('playVideo')

	const musics: MusicTrack[] = $derived(data.info?.Musics ?? [])
	const videos: Video[] = $derived(data.info?.Videos ?? [])
	// 只在載入時洗牌一次, 不要每次重新渲染都換
	const albums = $derived([...(data.info?.Albums ?? [])].sort(() => Math.random() - 0.5))
	const featured = $derived(albums.find((a: any) => a.cover_art) ?? albums[0])

	let streams = $state<StreamTrack[]>([])
	let playlists = $state<{ id: number; name: string; description: string | null }[]>([])

	const hour = new Date().getHours()
	const greeting = hour < 5 ? '夜深了' : hour < 12 ? '早安' : hour < 18 ? '午安' : '晚安'

	onMount(async () => {
		playerliststat.initialize()
		const [s, p] = await Promise.all([
			apiFetch('/file/streamtracks').then((r) => (r.ok ? r.json() : [])),
			apiFetch('/playlist/playlist').then((r) => (r.ok ? r.json() : []))
		])
		streams = s.map((t: StreamTrack) => ({ ...t, kind: 'stream' }))
		playlists = p
	})

	async function playAlbum(albumId: number) {
		const tracks = await fetchAlbumTracks(albumId)
		if (tracks.length) playMusiclist(tracks)
	}

	const music = (track: MusicTrack): PlayableTrack => ({ ...track, kind: 'music' })
</script>

<svelte:head>
	<title>首頁 - Lithium Player</title>
</svelte:head>

{#if data.error}
	<StatusMessage kind="error" title="載入失敗" message={data.error} retry={data.status === 500} />
{:else if musics.length === 0 && albums.length === 0 && videos.length === 0 && streams.length === 0}
	<StatusMessage
		icon={FolderSearch}
		title="媒體庫還是空的"
		message="到設定頁選擇音樂資料夾開始掃描, 或在播放清單貼上 YouTube / Bilibili 網址。"
	/>
	<div class="flex justify-center">
		<Button variant="primary" href="/app/setting">前往設定</Button>
	</div>
{:else}
	<div class="flex flex-col gap-10">
		<div>
			<h1 class="text-3xl font-bold tracking-tight">{greeting}</h1>
			<p class="mt-1 text-sm text-fg-muted">
				{new Date().toLocaleDateString('zh-TW', { month: 'long', day: 'numeric', weekday: 'long' })}
			</p>
		</div>

		<!-- 精選專輯 -->
		{#if featured}
			{@const cover = coverUrl(featured.cover_art, 600)}
			<section class="rounded-2xl border border-line/5 bg-surface">
				<div class="flex flex-col gap-6 p-6 sm:flex-row sm:items-end md:p-8">
					<a
						href="/app/albums/{featured.id}"
						class="block aspect-square w-40 shrink-0 overflow-hidden rounded-xl bg-surface-3 md:w-52"
					>
						{#if cover}
							<img src={cover} alt={featured.title} class="h-full w-full object-cover" />
						{:else}
							<Disc3 class="m-auto h-full w-1/3 text-fg-subtle" />
						{/if}
					</a>
					<div class="min-w-0">
						<p class="text-sm text-fg-muted">精選專輯</p>
						<h2 class="mt-2 line-clamp-2 text-3xl font-black tracking-tight md:text-5xl">
							{featured.title}
						</h2>
						<p class="mt-2 text-sm text-fg-muted">
							{featured.album_artist}
							{#if featured.release_date}· {featured.release_date}{/if}
							{#if featured.total_tracks}· {featured.total_tracks} 首{/if}
						</p>
						<div class="mt-5 flex gap-2">
							<Button variant="primary" size="lg" onclick={() => playAlbum(featured.id)}>
								<Play class="h-4 w-4" fill="currentColor" /> 播放
							</Button>
							<Button size="lg" href="/app/albums/{featured.id}">查看專輯</Button>
						</div>
					</div>
				</div>
			</section>
		{/if}

		<!-- 最新加入: 小卡片格子 -->
		{#if musics.length > 0}
			<section>
				<div class="mb-3 flex items-end justify-between">
					<h2 class="text-xl font-bold tracking-tight">最新加入</h2>
					<a href="/app/music" class="text-xs font-medium text-fg-muted hover:text-fg">查看全部</a>
				</div>
				<div class="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
					{#each musics.slice(0, 8) as track, i (track.id)}
						{@const cover = coverUrl(track.cover_art, 120)}
						<button
							class="group flex items-center gap-3 overflow-hidden rounded-lg bg-surface-2/60 pr-3 text-left transition-colors hover:bg-surface-3"
							onclick={() => playMusiclist(musics.slice(0, 8).map(music), i)}
						>
							<div class="relative h-14 w-14 shrink-0 bg-surface-3">
								{#if cover}
									<img src={cover} alt="" loading="lazy" class="h-full w-full object-cover" />
								{:else}
									<Music class="m-auto h-full w-5 text-fg-subtle" />
								{/if}
								<div
									class="absolute inset-0 grid place-items-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100"
								>
									<Play class="h-5 w-5 text-white" fill="currentColor" />
								</div>
							</div>
							<div class="min-w-0">
								<p class="truncate text-sm font-semibold">{track.title}</p>
								<p class="truncate text-xs text-fg-muted">{track.artist}</p>
							</div>
						</button>
					{/each}
				</div>
			</section>
		{/if}

		{#if albums.length > 0}
			<Shelf title="推薦專輯" href="/app/albums">
				{#snippet children(itemClass)}
					{#each albums as album (album.id)}
						<MediaCard
							class={itemClass}
							title={album.title}
							subtitle={album.album_artist}
							meta={album.total_tracks ? `${album.total_tracks} 首` : null}
							cover={coverUrl(album.cover_art, 400)}
							href="/app/albums/{album.id}"
							onplay={() => playAlbum(album.id)}
						/>
					{/each}
				{/snippet}
			</Shelf>
		{/if}

		{#if streams.length > 0}
			<Shelf title="網路音訊" itemClass="w-56 md:w-64">
				{#snippet children(itemClass)}
					{#each streams as track, i (track.id)}
						<MediaCard
							class={itemClass}
							shape="video"
							title={track.title}
							subtitle={track.artist}
							cover={track.cover_art}
							badge={platformLabel[track.platform]}
							onplay={() => playMusiclist(streams, i)}
						/>
					{/each}
				{/snippet}
			</Shelf>
		{/if}

		{#if playlists.length > 0}
			<Shelf title="你的播放清單" href="/app/playlist">
				{#snippet children(itemClass)}
					{#each playlists as playlist (playlist.id)}
						<MediaCard
							class={itemClass}
							title={playlist.name}
							subtitle={playlist.description ?? '播放清單'}
							href="/app/playlist/{playlist.id}"
							placeholder={ListMusic}
						/>
					{/each}
				{/snippet}
			</Shelf>
		{/if}

		{#if videos.length > 0}
			<Shelf title="影片" href="/app/video" itemClass="w-64 md:w-72">
				{#snippet children(itemClass)}
					{#each videos as video (video.id)}
						<MediaCard
							class={itemClass}
							shape="video"
							title={video.title}
							cover={coverUrl((video as any).thumbnail, 480)}
							placeholder={Clapperboard}
							onplay={() => playVideo(video)}
						/>
					{/each}
				{/snippet}
			</Shelf>
		{/if}
	</div>
{/if}
