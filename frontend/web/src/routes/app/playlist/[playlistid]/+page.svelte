<script lang="ts">
	import type { PageData } from './$types'
	import { Plus, Trash2, Play, Search } from 'lucide-svelte'
	import { APIUrl } from '$lib/api'
	import Cookies from 'js-cookie'

	let { data }: { data: PageData } = $props()
	const { playlist, error, status } = data
	let showAddDialog = $state(false)
	let searchQuery = $state('')
	let searchResults = $state({ musics: [], stream_tracks: [] })
	let searching = $state(false)

	function handleDelete(trackId: number) {
		// TODO: 刪除
	}

	function handlePlay(track: any) {
		// TODO: 播放
	}

	async function searchMusic() {
		if (!searchQuery) return
		searching = true
		const token = Cookies.get('access_token')
		try {
			const response = await fetch(
				`${APIUrl}/file/searchmusic?name=${encodeURIComponent(searchQuery)}`,
				{
					headers: {
						Authorization: `Bearer ${token}`
					}
				}
			)
			if (response.ok) {
				searchResults = await response.json()
			}
		} catch (e) {
			console.error(e)
		}
		searching = false
	}
	async function addToPlaylist(trackId: number, type: string) {
		const token = Cookies.get('access_token')
		const payload = {
			playlist_id: playlist.id,
			track_id: type === 'music' ? trackId : null,
			stream_id: type === 'stream' ? trackId : null
		}

		try {
			const response = await fetch(`${APIUrl}/playlist/playlist/${playlist.id}/`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(payload)
			})
			if (response.ok) {
				location.reload()
			}
		} catch (e) {
			console.error(e)
		}
	}
</script>

<div class="container mx-auto p-4">
	<div class="mb-6 flex items-center justify-between">
		<h1 class="text-2xl font-bold">{playlist.name}</h1>
		<button class="btn btn-primary" onclick={() => (showAddDialog = true)}>
			<Plus class="mr-2 h-4 w-4" />
			新增歌曲
		</button>
	</div>

	<div class="card bg-base-200">
		<div class="card-body p-0">
			{#if error}
				<div class="text-base-content/70 p-8 text-center">{error}</div>
			{:else if playlist.tracks && playlist.tracks.length > 0}
				<ul class="menu w-full">
					{#each playlist.tracks as track}
						<li class="border-b last:border-b-0">
							<div class="hover:bg-base-300 flex items-center justify-between p-4">
								<div class="flex flex-1 items-center">
									<button class="btn btn-ghost btn-sm btn-circle" onclick={() => handlePlay(track)}>
										<Play class="h-4 w-4" />
									</button>
									<div class="ml-4">
										<div class="font-medium">{track.track.title}</div>
										<div class="text-sm opacity-70">{track.track.artist}</div>
									</div>
								</div>
								<!-- <button
									class="btn btn-ghost btn-sm btn-circle"
									onclick={() => handleDelete(track.track.id)}
								>
									<Trash2 class="text-error h-4 w-4" />
								</button> -->
							</div>
						</li>
					{/each}
				</ul>
			{:else}
				<div class="text-base-content/70 p-8 text-center">此播放清單還沒有歌曲</div>
			{/if}
		</div>
	</div>
</div>

{#if showAddDialog}
	<div class="modal modal-open">
		<div class="modal-box">
			<h3 class="mb-4 text-lg font-bold">新增歌曲至播放清單</h3>
			<div class="form-control">
				<div class="input-group flex">
					<input
						type="text"
						placeholder="搜尋歌曲..."
						class="input input-bordered w-full"
						bind:value={searchQuery}
					/>
					<button class="btn btn-square" onclick={searchMusic}>
						<Search />
					</button>
				</div>
			</div>

			{#if searching}
				<div class="mt-4 text-center">
					<span class="loading loading-spinner"></span>
				</div>
			{:else if searchResults.musics.length > 0 || searchResults.stream_tracks.length > 0}
				<ul class="menu bg-base-200 rounded-box mt-4">
					{#each searchResults.musics as music}
						<li>
							<button
								class="hover:bg-base-300 flex items-center justify-between p-3"
								onclick={() => addToPlaylist(music.id, 'music')}
							>
								<div>
									<div class="font-medium">{music.title}</div>
									<div class="text-sm opacity-70">{music.artist}</div>
								</div>
								<Plus class="h-4 w-4" />
							</button>
						</li>
					{/each}
					{#each searchResults.stream_tracks as track}
						<li>
							<button
								class="hover:bg-base-300 flex items-center justify-between p-3"
								onclick={() => addToPlaylist(track.id, 'stream')}
							>
								<div>
									<div class="font-medium">{track.title}</div>
									<div class="text-sm opacity-70">{track.artist}</div>
								</div>
								<Plus class="h-4 w-4" />
							</button>
						</li>
					{/each}
				</ul>
			{/if}

			<div class="modal-action">
				<button class="btn" onclick={() => (showAddDialog = false)}>取消</button>
			</div>
		</div>
	</div>
{/if}
