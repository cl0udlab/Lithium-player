<script lang="ts">
	import { Tv } from 'lucide-svelte'
	import { coverUrl } from '$lib/api'
	import MediaCard from '$lib/components/ui/MediaCard.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const animes: any[] = $derived(data.animes ?? [])
</script>

<svelte:head>
	<title>動畫 - Lithium Player</title>
</svelte:head>

<PageHeader title="動畫" subtitle="{animes.length} 部" />
{#if animes.length}
	<div class="grid grid-cols-2 gap-x-5 gap-y-7 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6">
		{#each animes as anime (anime.id)}
			<MediaCard
				shape="portrait"
				title={anime.title}
				subtitle={anime.release_date}
				meta={anime.total_episodes ? `${anime.total_episodes} 集` : null}
				cover={coverUrl(anime.cover_image, 400)}
				href="/app/anime/{anime.id}"
				placeholder={Tv}
			/>
		{/each}
	</div>
{:else}
	<StatusMessage icon={Tv} title="還沒有動畫" message="掃描影片資料夾時會自動辨識動畫。" />
{/if}
