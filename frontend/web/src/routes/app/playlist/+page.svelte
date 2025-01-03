<script lang="ts">
	import type { PageData } from './$types'
	import { getContext } from 'svelte'
	import { APIUrl } from '$lib/api'
	import Cookies from 'js-cookie'
	import { goto } from '$app/navigation'

	let { data }: { data: PageData } = $props()
	const { playlist, error, status } = data
	const playMusiclist = getContext('playMusiclist')
	let showDialog = $state(false)
	let newPlaylistName = $state('')

	async function createPlaylist() {
		const token = Cookies.get('access_token')
		const response = await fetch(`${APIUrl}/playlist/playlist`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${token}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ name: newPlaylistName })
		})

		if (response.ok) {
			location.reload()
		}
		showDialog = false
		newPlaylistName = ''
	}
</script>

<div class="mb-8">
	<div class="mb-4 flex items-center justify-between">
		<h1 class="text-2xl font-bold">播放清單</h1>
		<button class="btn btn-primary" onclick={() => (showDialog = true)}> 新增播放清單 </button>
	</div>
	{#if showDialog}
		<div class="modal modal-open">
			<div class="modal-box">
				<h3 class="text-lg font-bold">新增播放清單</h3>
				<input
					type="text"
					placeholder="輸入播放清單名稱"
					class="input input-bordered mt-4 w-full"
					onkeydown={(e) => e.key === 'Enter' && createPlaylist()}
					bind:value={newPlaylistName}
				/>
				<div class="modal-action">
					<button class="btn" onclick={() => (showDialog = false)}>取消</button>
					<button class="btn btn-primary" onclick={createPlaylist}>確定</button>
				</div>
			</div>
		</div>
	{/if}
	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
		{#each playlist as playlist}
			<button
				class="card card-compact bg-base-200 shadow-xl transition-all hover:shadow-2xl"
				onclick={() => goto(`/app/playlist/${playlist.id}`)}
				onkeydown={(e) => e.key === 'Enter' && goto(`/app/playlist/${playlist.id}`)}
			>
				<div class="card-body">
					<h2 class="card-title">{playlist.name}</h2>
					{#if playlist.description}
						<p class="text-sm opacity-75">{playlist.description}</p>
					{/if}
				</div>
			</button>
		{/each}
	</div>
</div>
