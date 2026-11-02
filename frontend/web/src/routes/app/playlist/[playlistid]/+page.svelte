<script lang="ts">
	import { getContext } from 'svelte'
	import { goto, invalidateAll } from '$app/navigation'
	import { Plus, Play, Shuffle, Search, Link, Trash2, ListMusic, Music, Radio } from 'lucide-svelte'
	import { apiFetch, coverUrl } from '$lib/api'
	import { toast } from '$lib/stores/toast.svelte'
	import type { PlayableTrack } from '$lib/types'
	import Button from '$lib/components/ui/Button.svelte'
	import Dialog from '$lib/components/ui/Dialog.svelte'
	import Input from '$lib/components/ui/Input.svelte'
	import Spinner from '$lib/components/ui/Spinner.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import Tabs from '$lib/components/ui/Tabs.svelte'
	import TrackList from '$lib/components/ui/TrackList.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playMusiclist = getContext<(tracks: PlayableTrack[], startIndex?: number) => void>(
		'playMusiclist'
	)

	const playlist = $derived(data.playlist as any)
	const items: any[] = $derived(playlist?.tracks ?? [])
	// API 回傳的播放清單項目轉成播放器可用的格式
	const tracks: PlayableTrack[] = $derived(
		items.map((item) =>
			item.track_type === 'stream'
				? { ...item.streamtrack, kind: 'stream' }
				: { ...item.track, kind: 'music' }
		)
	)
	const cover = $derived(coverUrl(tracks.find((t) => t.cover_art)?.cover_art, 600))

	let addOpen = $state(false)
	let addMode = $state<'search' | 'url'>('search')
	let deleteOpen = $state(false)

	type SearchItem = { id: number; title: string; artist: string }
	let searchQuery = $state('')
	let searching = $state(false)
	let searchResults = $state<{ musics: SearchItem[]; stream_tracks: SearchItem[] }>({
		musics: [],
		stream_tracks: []
	})
	let urlInput = $state('')
	let urlLoading = $state(false)

	async function searchMusic(e?: SubmitEvent) {
		e?.preventDefault()
		if (!searchQuery.trim()) return
		searching = true
		try {
			const response = await apiFetch(`/file/searchmusic?name=${encodeURIComponent(searchQuery)}`)
			if (response.ok) searchResults = await response.json()
		} finally {
			searching = false
		}
	}

	async function addToPlaylist(item: SearchItem, type: 'music' | 'stream') {
		const response = await apiFetch(`/playlist/playlist/${playlist.id}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				track_id: type === 'music' ? item.id : null,
				stream_id: type === 'stream' ? item.id : null
			})
		})
		if (response.ok) {
			toast.success('已加入播放清單', item.title)
			await invalidateAll()
		} else {
			const body = await response.json().catch(() => null)
			toast.error('加入失敗', body?.detail)
		}
	}

	async function addUrl(e?: SubmitEvent) {
		e?.preventDefault()
		if (!urlInput.trim()) return
		urlLoading = true
		try {
			const response = await apiFetch(`/playlist/playlist/${playlist.id}/url`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ url: urlInput.trim() })
			})
			const body = await response.json().catch(() => null)
			if (!response.ok) {
				toast.error('無法加入網址', body?.detail ?? `HTTP ${response.status}`)
				return
			}
			toast.success(
				`已加入 ${body.added} 首`,
				body.total > body.added ? `${body.total - body.added} 首已經在清單中` : undefined
			)
			urlInput = ''
			addOpen = false
			await invalidateAll()
		} finally {
			urlLoading = false
		}
	}

	async function removeTrack(index: number) {
		const item = items[index]
		const response = await apiFetch(`/playlist/playlist/${playlist.id}/track/${item.position}`, {
			method: 'DELETE'
		})
		if (response.ok) {
			toast.info('已移除', tracks[index].title)
			await invalidateAll()
		} else {
			toast.error('移除失敗')
		}
	}

	async function deletePlaylist() {
		const response = await apiFetch(`/playlist/playlist/${playlist.id}`, { method: 'DELETE' })
		if (response.ok) {
			toast.info('已刪除播放清單', playlist.name)
			goto('/app/playlist')
		} else {
			toast.error('刪除失敗')
		}
	}
</script>

<svelte:head>
	<title>{playlist?.name ?? '播放清單'} - Lithium Player</title>
</svelte:head>

{#snippet resultRow(item: SearchItem, type: 'music' | 'stream')}
	<button
		class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left hover:bg-line/5"
		onclick={() => addToPlaylist(item, type)}
	>
		{#if type === 'music'}
			<Music class="h-4 w-4 shrink-0 text-fg-subtle" />
		{:else}
			<Radio class="h-4 w-4 shrink-0 text-fg-subtle" />
		{/if}
		<div class="min-w-0 flex-1">
			<p class="truncate text-sm">{item.title}</p>
			<p class="truncate text-xs text-fg-muted">{item.artist}</p>
		</div>
		<Plus class="h-4 w-4 shrink-0 text-fg-subtle" />
	</button>
{/snippet}

{#if data.error}
	<StatusMessage kind="error" title="載入失敗" message={data.error} retry={data.status === 500} />
{:else}
	<section class="mb-8 pt-4">
		<div class="relative flex flex-col gap-6 sm:flex-row sm:items-end">
			<div
				class="grid aspect-square w-44 shrink-0 place-items-center overflow-hidden rounded-2xl bg-surface-3 md:w-56"
			>
				{#if cover}
					<img src={cover} alt="" referrerpolicy="no-referrer" class="h-full w-full object-cover" />
				{:else}
					<ListMusic class="h-1/3 w-1/3 text-fg-subtle" />
				{/if}
			</div>
			<div class="min-w-0">
				<p class="text-sm text-fg-muted">播放清單</p>
				<h1 class="mt-2 text-4xl font-black tracking-tight md:text-6xl">{playlist.name}</h1>
				<p class="mt-3 text-sm text-fg-muted">{tracks.length} 首</p>
				<div class="mt-5 flex flex-wrap gap-2">
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
					<Button size="lg" onclick={() => (addOpen = true)}>
						<Plus class="h-4 w-4" /> 新增歌曲
					</Button>
					<Button size="icon" variant="ghost" onclick={() => (deleteOpen = true)} aria-label="刪除播放清單">
						<Trash2 class="h-4 w-4" />
					</Button>
				</div>
			</div>
		</div>
	</section>

	{#if tracks.length}
		<TrackList {tracks} onplay={(i) => playMusiclist(tracks, i)}>
			{#snippet actions(_track, i)}
				<button
					class="grid h-7 w-7 place-items-center rounded-full hover:bg-danger/15 hover:text-danger"
					onclick={() => removeTrack(i)}
					aria-label="從播放清單移除"
				>
					<Trash2 class="h-3.5 w-3.5" />
				</button>
			{/snippet}
		</TrackList>
	{:else}
		<StatusMessage title="這個播放清單還沒有歌曲" message="點「新增歌曲」從音樂庫加入, 或貼上 YouTube / Bilibili 網址。" />
	{/if}
{/if}

<Dialog bind:open={addOpen} title="新增歌曲" class="w-[min(36rem,calc(100vw-2rem))]">
	<Tabs
		bind:value={addMode}
		items={[
			{ value: 'search', label: '搜尋音樂庫', icon: Search },
			{ value: 'url', label: '網址', icon: Link }
		]}
	>
		{#snippet content(mode)}
			{#if mode === 'search'}
				<form class="flex gap-2" onsubmit={searchMusic}>
					<Input bind:value={searchQuery} icon={Search} placeholder="歌名、歌手、專輯…" class="flex-1" />
					<Button type="submit" disabled={searching}>搜尋</Button>
				</form>
				<div class="mt-3 max-h-80 overflow-y-auto">
					{#if searching}
						<div class="grid place-items-center py-8"><Spinner /></div>
					{:else}
						{#each searchResults.musics as item (item.id)}
							{@render resultRow(item, 'music')}
						{/each}
						{#each searchResults.stream_tracks as item (item.id)}
							{@render resultRow(item, 'stream')}
						{/each}
					{/if}
				</div>
			{:else}
				<form class="flex flex-col gap-3" onsubmit={addUrl}>
					<Input
						type="url"
						bind:value={urlInput}
						icon={Link}
						placeholder="https://www.youtube.com/watch?v=…"
						disabled={urlLoading}
					/>
					<p class="text-xs text-fg-subtle">
						支援 YouTube、Bilibili 和直接的音訊連結; 貼上播放清單網址會一次加入整份清單。
					</p>
					<Button variant="primary" type="submit" disabled={urlLoading || !urlInput.trim()}>
						{#if urlLoading}<Spinner class="h-4 w-4" /> 解析中…{:else}<Plus class="h-4 w-4" /> 加入{/if}
					</Button>
				</form>
			{/if}
		{/snippet}
	</Tabs>
</Dialog>

<Dialog bind:open={deleteOpen} title="刪除播放清單?" description="「{playlist?.name}」會被永久刪除, 裡面的歌曲不會受影響。">
	<div></div>
	{#snippet footer()}
		<Button variant="ghost" onclick={() => (deleteOpen = false)}>取消</Button>
		<Button variant="danger" onclick={deletePlaylist}>刪除</Button>
	{/snippet}
</Dialog>
