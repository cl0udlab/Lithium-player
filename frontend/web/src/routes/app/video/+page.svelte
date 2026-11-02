<script lang="ts">
	import { getContext } from 'svelte'
	import { Clapperboard } from 'lucide-svelte'
	import { coverUrl } from '$lib/api'
	import { formatDuration } from '$lib/utils/library'
	import type { Video } from '$lib/types'
	import MediaCard from '$lib/components/ui/MediaCard.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playVideo = getContext<(video: Video) => void>('playVideo')
	const videos: any[] = $derived(data.videos ?? [])
</script>

<svelte:head>
	<title>影片 - Lithium Player</title>
</svelte:head>

{#if data.error}
	<StatusMessage kind="error" title="載入失敗" message={data.error} retry={data.status === 500} />
{:else}
	<PageHeader title="影片" subtitle="{videos.length} 部" />
	{#if videos.length}
		<div class="grid grid-cols-1 gap-x-5 gap-y-7 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
			{#each videos as video (video.id)}
				<MediaCard
					shape="video"
					title={video.title}
					subtitle={video.description}
					meta={formatDuration(video.duration)}
					cover={coverUrl(video.thumbnail, 640)}
					placeholder={Clapperboard}
					onplay={() => playVideo(video)}
				/>
			{/each}
		</div>
	{:else}
		<StatusMessage icon={Clapperboard} title="還沒有影片" message="到設定頁掃描影片資料夾。" />
	{/if}
{/if}
