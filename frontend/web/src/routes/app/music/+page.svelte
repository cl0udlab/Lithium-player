<script lang="ts">
	import { apiFetch } from '$lib/api'
	import { toast } from '$lib/stores/toast.svelte'
	import LibraryToolbar from '$lib/components/ui/LibraryToolbar.svelte'
	import { getContext } from 'svelte'
	import { Play, Shuffle } from 'lucide-svelte'
	import type { MusicTrack, PlayableTrack } from '$lib/types'
	import Button from '$lib/components/ui/Button.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import TrackList from '$lib/components/ui/TrackList.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playMusiclist =
		getContext<(tracks: PlayableTrack[], startIndex?: number) => void>('playMusiclist')
	const tracks: PlayableTrack[] = $derived(
		((data.musics ?? []) as PlayableTrack[]).map((t) =>
			t.kind === 'stream' ? t : { ...t, kind: 'music' as const }
		)
	)

	function shuffle() {
		playMusiclist([...tracks].sort(() => Math.random() - 0.5))
	}
</script>

<svelte:head>
	<title>歌曲 - Lithium Player</title>
</svelte:head>

{#if data.error}
	<StatusMessage kind="error" title="載入失敗" message={data.error} retry={data.status === 500} />
{:else}
	<PageHeader title="歌曲" subtitle="{data.total} 首">
		{#snippet actions()}
			<Button onclick={shuffle} disabled={!tracks.length}>
				<Shuffle class="h-4 w-4" /> 隨機播放
			</Button>
			<Button variant="primary" onclick={() => playMusiclist(tracks)} disabled={!tracks.length}>
				<Play class="h-4 w-4" fill="currentColor" /> 播放本頁
			</Button>
		{/snippet}
	</PageHeader>
	<LibraryToolbar
		path="/app/music"
		total={data.total}
		page={data.page}
		size={data.size}
		q={data.q}
		cached={data.cached}
		offlineFilter
	/>
	{#if tracks.length}
		<TrackList {tracks} onplay={(i) => playMusiclist(tracks, i)}>
			{#snippet actions(track)}
				{#if track.kind === 'stream' && track.url.startsWith('subsonic://')}
					<Button
						size="sm"
						disabled={track.cached}
						onclick={async () => {
							try {
								const response = await apiFetch(`/subsonic/cache/${track.id}`, { method: 'POST' })
								if (!response.ok) {
									const body = await response.json()
									throw new Error(body.detail || '快取失敗')
								}
								track.cached = true
								toast.success(`已快取「${track.title}」`)
							} catch (error) {
								toast.error(error instanceof Error ? error.message : '快取失敗')
							}
						}}>{track.cached ? '已快取' : '快取'}</Button
					>
				{/if}
			{/snippet}
		</TrackList>
	{:else}
		<StatusMessage
			title="還沒有歌曲"
			message="可到設定頁掃描資料夾或同步 Subsonic，亦可調整搜尋條件。"
		/>
	{/if}
{/if}
