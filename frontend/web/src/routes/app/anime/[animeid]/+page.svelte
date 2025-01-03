<script lang="ts">
	import type { PageData } from './$types'
	let { data }: { data: PageData } = $props()
  	import { APIUrl } from '$lib/api'
  const { animes } = data
  function getCoverUrl(coverId: string | null) {
		if (!coverId) return '/placeholder.png'
		return `${APIUrl}/file/image?image_id=${coverId}&image_size=500`
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="flex flex-col gap-8 md:flex-row">
		<div class="w-full md:w-1/4">
			{#if animes.cover_image}
				<img src={animes.cover_image} alt={animes.title} class="w-full rounded-lg shadow-lg" />
			{:else}
				<div class="flex aspect-[3/4] w-full items-center justify-center rounded-lg bg-gray-200">
					<span class="text-gray-400">無封面</span>
				</div>
			{/if}
		</div>

		<div class="flex-1">
			<h1 class="mb-4 text-3xl font-bold">{animes.title}</h1>
			{#if animes.original_title}
				<h2 class="mb-4 text-xl text-gray-600">{animes.original_title}</h2>
			{/if}

			<div class="mb-4">
				<p class="text-gray-700">{animes.description || '暫無簡介'}</p>
			</div>

			<div class="mb-4 grid grid-cols-2 gap-4">
				<div>
					<span class="font-semibold">放送日期：</span>
					<span>{animes.release_date}</span>
				</div>
				{#if animes.studio}
					<div>
						<span class="font-semibold">製作公司：</span>
						<span>{animes.studio}</span>
					</div>
				{/if}
				{#if animes.author}
					<div>
						<span class="font-semibold">原作：</span>
						<span>{animes.author}</span>
					</div>
				{/if}
			</div>


			<div class="mb-4 flex flex-wrap gap-2">
				{#each animes.tags as tag}
					<span class="rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800">
						{tag.name}
					</span>
				{/each}
			</div>
		</div>
	</div>


	<div class="mt-8">
		<h2 class="mb-4 text-2xl font-bold">劇集列表</h2>
		<div class="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
			{#each animes.episodes as episode}
				<div class="overflow-hidden rounded-lg bg-white shadow">
					{#if episode.thumbnail}
						<img
							src={getCoverUrl(episode.thumbnail)}
							alt={episode.title}
							class="aspect-video w-full object-cover"
						/>
					{:else}
						<div class="aspect-video w-full bg-gray-200"></div>
					{/if}
					<div class="p-4">
						<h3 class="font-semibold">第 {episode.episode_number} 集</h3>
						{#if episode.title}
							<p class="text-sm text-gray-600">{episode.title}</p>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</div>
</div>
