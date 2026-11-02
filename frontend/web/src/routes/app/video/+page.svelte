<script lang="ts">
	import { getContext } from 'svelte'
	import { invalidateAll } from '$app/navigation'
	import { Clapperboard, RefreshCw, Search, Trash2 } from 'lucide-svelte'
	import { coverUrl } from '$lib/api'
	import { formatDuration } from '$lib/utils/library'
	import { toast } from '$lib/stores/toast.svelte'
	import { deleteVideo, refreshVideo, type BangumiCandidate } from '$lib/video'
	import type { Video } from '$lib/types'
	import ActionMenu from '$lib/components/ui/ActionMenu.svelte'
	import BangumiMatchDialog from '$lib/components/BangumiMatchDialog.svelte'
	import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte'
	import MediaCard from '$lib/components/ui/MediaCard.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playVideo = getContext<(video: Video) => void>('playVideo')
	const videos: any[] = $derived(data.videos ?? [])

	let target = $state<any>(null)
	let matchOpen = $state(false)
	let deleteOpen = $state(false)

	async function rescrape(video: any) {
		toast.info('正在重新刮削', video.title)
		const result = await refreshVideo(video.id)
		if (!result.ok) return toast.error('重新刮削失敗', result.detail)
		toast.success('已更新 metadata', video.title)
		await invalidateAll()
	}

	async function match(candidate: BangumiCandidate) {
		const result = await refreshVideo(target.id, { bangumi_id: candidate.id })
		if (!result.ok) {
			toast.error('配對失敗', result.detail)
			return false
		}
		toast.success('已配對', candidate.name_cn || candidate.name)
		await invalidateAll()
		return true
	}

	async function remove() {
		const result = await deleteVideo(target.id)
		if (!result.ok) return toast.error('移除失敗', result.detail)
		toast.info('已從媒體庫移除', target.title)
		await invalidateAll()
	}
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
				>
					{#snippet actions()}
						<ActionMenu
							label="{video.title} 的操作"
							items={[
								{ label: '重新刮削', icon: RefreshCw, onselect: () => rescrape(video) },
								{
									label: '手動配對動畫',
									icon: Search,
									onselect: () => ((target = video), (matchOpen = true))
								},
								{
									label: '從媒體庫移除',
									icon: Trash2,
									danger: true,
									onselect: () => ((target = video), (deleteOpen = true))
								}
							]}
						/>
					{/snippet}
				</MediaCard>
			{/each}
		</div>
	{:else}
		<StatusMessage icon={Clapperboard} title="還沒有影片" message="到設定頁掃描影片資料夾。" />
	{/if}
{/if}

<BangumiMatchDialog
	bind:open={matchOpen}
	query={target?.series?.title ?? target?.title ?? ''}
	onselect={match}
/>

<ConfirmDialog
	bind:open={deleteOpen}
	title="從媒體庫移除？"
	message="「{target?.title}」會從媒體庫移除，硬碟上的檔案不會被刪除。重新掃描時會再加回來。"
	confirmLabel="移除"
	onconfirm={remove}
/>
