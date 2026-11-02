<script lang="ts">
	import { getContext } from 'svelte'
	import { Play, Shuffle } from 'lucide-svelte'
	import type { MusicTrack, PlayableTrack } from '$lib/types'
	import Button from '$lib/components/ui/Button.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import TrackList from '$lib/components/ui/TrackList.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playMusiclist = getContext<(tracks: PlayableTrack[], startIndex?: number) => void>(
		'playMusiclist'
	)
	const tracks: PlayableTrack[] = $derived(
		((data.musics ?? []) as MusicTrack[]).map((t) => ({ ...t, kind: 'music' }))
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
	<PageHeader title="歌曲" subtitle="{tracks.length} 首">
		{#snippet actions()}
			<Button onclick={shuffle} disabled={!tracks.length}>
				<Shuffle class="h-4 w-4" /> 隨機播放
			</Button>
			<Button variant="primary" onclick={() => playMusiclist(tracks)} disabled={!tracks.length}>
				<Play class="h-4 w-4" fill="currentColor" /> 播放全部
			</Button>
		{/snippet}
	</PageHeader>
	{#if tracks.length}
		<TrackList {tracks} onplay={(i) => playMusiclist(tracks, i)} />
	{:else}
		<StatusMessage title="還沒有歌曲" message="到設定頁掃描音樂資料夾。" />
	{/if}
{/if}
