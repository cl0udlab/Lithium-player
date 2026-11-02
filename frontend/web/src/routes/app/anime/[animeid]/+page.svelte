<script lang="ts">
	import { getContext } from 'svelte'
	import { goto, invalidateAll } from '$app/navigation'
	import { Tv, Play, RefreshCw, Search, Trash2 } from 'lucide-svelte'
	import { coverUrl } from '$lib/api'
	import { toast } from '$lib/stores/toast.svelte'
	import {
		deleteAnime,
		deleteVideo,
		refreshAnime,
		refreshVideo,
		type BangumiCandidate
	} from '$lib/video'
	import type { Video } from '$lib/types'
	import ActionMenu from '$lib/components/ui/ActionMenu.svelte'
	import BangumiMatchDialog from '$lib/components/BangumiMatchDialog.svelte'
	import Button from '$lib/components/ui/Button.svelte'
	import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playVideo = getContext<(video: Video) => void>('playVideo')
	const anime: any = $derived(data.animes)
	const cover = $derived(coverUrl(anime.cover_image, 600))
	const episodes: any[] = $derived(
		[...(anime.episodes ?? [])].sort((a, b) => (a.episode_number ?? 0) - (b.episode_number ?? 0))
	)

	let refreshing = $state(false)
	let matchOpen = $state(false)
	let deleteAnimeOpen = $state(false)
	let episodeTarget = $state<any>(null)
	let deleteEpisodeOpen = $state(false)

	async function afterSeriesChange(newId: number | null) {
		if (newId === null) return goto('/app/anime')
		if (newId !== anime.id) return goto(`/app/anime/${newId}`)
		await invalidateAll()
	}

	async function rescrapeAnime() {
		refreshing = true
		toast.info('正在重新刮削', `${anime.title}，共 ${episodes.length} 集`)
		try {
			const result = await refreshAnime(anime.id)
			if (!result.ok) return toast.error('重新刮削失敗', result.detail)
			toast.success('已更新 metadata', anime.title)
			await afterSeriesChange(result.data.id)
		} finally {
			refreshing = false
		}
	}

	async function match(candidate: BangumiCandidate) {
		const result = await refreshAnime(anime.id, { bangumi_id: candidate.id })
		if (!result.ok) {
			toast.error('配對失敗', result.detail)
			return false
		}
		toast.success('已配對', candidate.name_cn || candidate.name)
		await afterSeriesChange(result.data.id)
		return true
	}

	async function removeAnime() {
		const result = await deleteAnime(anime.id)
		if (!result.ok) return toast.error('移除失敗', result.detail)
		toast.info('已從媒體庫移除', anime.title)
		await goto('/app/anime')
	}

	async function rescrapeEpisode(episode: any) {
		toast.info('正在重新刮削', `第 ${episode.episode_number} 集`)
		const result = await refreshVideo(episode.id)
		if (!result.ok) return toast.error('重新刮削失敗', result.detail)
		toast.success('已更新 metadata', `第 ${episode.episode_number} 集`)

		if (episodes.length === 1) return afterSeriesChange(result.data.series_id)
		await invalidateAll()
	}

	async function removeEpisode() {
		const result = await deleteVideo(episodeTarget.id)
		if (!result.ok) return toast.error('移除失敗', result.detail)
		toast.info('已從媒體庫移除', `第 ${episodeTarget.episode_number} 集`)

		if (episodes.length === 1) return goto('/app/anime')
		await invalidateAll()
	}
</script>

<svelte:head>
	<title>{anime.title} - Lithium Player</title>
</svelte:head>

<section class="mb-8 pt-4">
	<div class="relative flex flex-col gap-8 md:flex-row">
		<div class="aspect-[3/4] w-44 shrink-0 overflow-hidden rounded-2xl bg-surface-3 md:w-56">
			{#if cover}
				<img src={cover} alt={anime.title} class="h-full w-full object-cover" />
			{:else}
				<Tv class="m-auto h-full w-1/3 text-fg-subtle" />
			{/if}
		</div>
		<div class="min-w-0 flex-1">
			<p class="text-sm text-fg-muted">動畫</p>
			<h1 class="mt-2 text-4xl font-black tracking-tight">{anime.title}</h1>
			{#if anime.original_title}
				<p class="mt-1 text-lg text-fg-muted">{anime.original_title}</p>
			{/if}
			<dl class="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
				{#each [['放送日期', anime.release_date], ['製作公司', anime.studio], ['原作', anime.author]] as [label, value]}
					{#if value}
						<div>
							<dt class="text-xs text-fg-subtle">{label}</dt>
							<dd>{value}</dd>
						</div>
					{/if}
				{/each}
			</dl>
			<p class="mt-4 max-w-3xl text-sm leading-relaxed text-fg-muted">
				{anime.description || '暫無簡介'}
			</p>
			{#if anime.tags?.length}
				<div class="mt-4 flex flex-wrap gap-2">
					{#each anime.tags as tag (tag.id ?? tag.name)}
						<span
							class="rounded-full border border-line/10 bg-surface-2 px-3 py-1 text-xs text-fg-muted"
						>
							{tag.name}
						</span>
					{/each}
				</div>
			{/if}
			<div class="mt-6 flex flex-wrap gap-2">
				<Button size="sm" disabled={refreshing} onclick={rescrapeAnime}>
					<RefreshCw class="h-3.5 w-3.5 {refreshing ? 'animate-spin' : ''}" /> 重新刮削
				</Button>
				<Button size="sm" disabled={refreshing} onclick={() => (matchOpen = true)}>
					<Search class="h-3.5 w-3.5" /> 手動配對
				</Button>
				<Button
					size="sm"
					variant="danger"
					disabled={refreshing}
					onclick={() => (deleteAnimeOpen = true)}
				>
					<Trash2 class="h-3.5 w-3.5" /> 從媒體庫移除
				</Button>
			</div>
		</div>
	</div>
</section>

<h2 class="mb-4 text-xl font-bold tracking-tight">劇集 · {episodes.length}</h2>
<div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
	{#each episodes as episode (episode.id)}
		<div class="group relative">
			<button class="w-full text-left" onclick={() => playVideo(episode)}>
				<div class="relative aspect-video overflow-hidden rounded-xl bg-surface-2">
					{#if episode.thumbnail}
						<img
							src={coverUrl(episode.thumbnail, 480)}
							alt=""
							loading="lazy"
							class="h-full w-full object-cover"
						/>
					{/if}
					<div
						class="absolute inset-0 grid place-items-center bg-black/0 transition-colors group-hover:bg-black/40"
					>
						<Play
							class="h-8 w-8 text-white opacity-0 transition-opacity group-hover:opacity-100"
							fill="currentColor"
						/>
					</div>
				</div>
				<p class="mt-2 text-sm font-semibold">第 {episode.episode_number} 集</p>
				{#if episode.title}
					<p class="truncate text-xs text-fg-muted">{episode.title}</p>
				{/if}
			</button>
			<div
				class="absolute top-2 right-2 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100 has-[[aria-expanded=true]]:opacity-100"
			>
				<ActionMenu
					label="第 {episode.episode_number} 集的操作"
					items={[
						{ label: '重新刮削', icon: RefreshCw, onselect: () => rescrapeEpisode(episode) },
						{
							label: '從媒體庫移除',
							icon: Trash2,
							danger: true,
							onselect: () => ((episodeTarget = episode), (deleteEpisodeOpen = true))
						}
					]}
				/>
			</div>
		</div>
	{/each}
</div>

<BangumiMatchDialog
	bind:open={matchOpen}
	query={anime.original_title || anime.title}
	description="整部動畫的 {episodes.length} 集都會改配對到選擇的條目。"
	onselect={match}
/>

<ConfirmDialog
	bind:open={deleteAnimeOpen}
	title="移除整部動畫？"
	message="「{anime.title}」和全部 {episodes.length} 集會從媒體庫移除，硬碟上的檔案不會被刪除。"
	confirmLabel="移除"
	onconfirm={removeAnime}
/>

<ConfirmDialog
	bind:open={deleteEpisodeOpen}
	title="移除這一集？"
	message="第 {episodeTarget?.episode_number} 集會從媒體庫移除，硬碟上的檔案不會被刪除。"
	confirmLabel="移除"
	onconfirm={removeEpisode}
/>
