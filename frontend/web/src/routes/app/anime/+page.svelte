<script lang="ts">
	import type { PageData } from './$types'
	import { APIUrl } from '$lib/api'

	let { data }: { data: PageData } = $props()

	function getCoverUrl(coverId: string | null) {
		if (!coverId) return '/placeholder.png'
		return `${APIUrl}/file/image?image_id=${coverId}&image_size=300`
	}
</script>

<div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
	{#each data.animes as anime}
		<div class="card bg-base-200 shadow-xl transition-transform hover:scale-105">
			<figure class="h-48">
				{#if anime.cover_image}
					<img
						src={getCoverUrl(anime.cover_image)}
						alt={anime.title}
						class="h-full w-full object-cover"
					/>
				{/if}
			</figure>
			<div class="card-body">
				<h2 class="card-title text-lg">{anime.title}</h2>
				<p class="line-clamp-2 text-sm opacity-75">{anime.description}</p>
			</div>
		</div>
	{/each}
</div>
