<script lang="ts">
	import { goto } from '$app/navigation'
	import { Plus, ListMusic } from 'lucide-svelte'
	import { apiFetch } from '$lib/api'
	import { toast } from '$lib/stores/toast.svelte'
	import Button from '$lib/components/ui/Button.svelte'
	import Dialog from '$lib/components/ui/Dialog.svelte'
	import Input from '$lib/components/ui/Input.svelte'
	import MediaCard from '$lib/components/ui/MediaCard.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const playlists: any[] = $derived(Array.isArray(data.playlist) ? data.playlist : [])
	let dialogOpen = $state(false)
	let name = $state('')
	let creating = $state(false)

	async function createPlaylist(e?: SubmitEvent) {
		e?.preventDefault()
		if (!name.trim()) return
		creating = true
		const response = await apiFetch('/playlist/playlist', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name: name.trim() })
		})
		creating = false
		if (!response.ok) {
			toast.error('建立失敗', `HTTP ${response.status}`)
			return
		}
		const created = await response.json()
		dialogOpen = false
		name = ''
		toast.success('已建立播放清單', created.name)
		goto(`/app/playlist/${created.id}`)
	}
</script>

<svelte:head>
	<title>播放清單 - Lithium Player</title>
</svelte:head>

{#if data.error}
	<StatusMessage kind="error" title="載入失敗" message={data.error} retry={data.status === 500} />
{:else}
	<PageHeader title="播放清單" subtitle="{playlists.length} 個">
		{#snippet actions()}
			<Button variant="primary" onclick={() => (dialogOpen = true)}>
				<Plus class="h-4 w-4" /> 新增播放清單
			</Button>
		{/snippet}
	</PageHeader>

	{#if playlists.length}
		<div class="grid grid-cols-2 gap-x-5 gap-y-7 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6">
			{#each playlists as playlist (playlist.id)}
				<MediaCard
					title={playlist.name}
					subtitle={playlist.description ?? '播放清單'}
					href="/app/playlist/{playlist.id}"
					placeholder={ListMusic}
				/>
			{/each}
		</div>
	{:else}
		<StatusMessage
			icon={ListMusic}
			title="還沒有播放清單"
			message="建立一個播放清單, 可以混合本機音樂和 YouTube / Bilibili 網址。"
		/>
	{/if}
{/if}

<Dialog bind:open={dialogOpen} title="新增播放清單">
	<form id="create-playlist" onsubmit={createPlaylist}>
		<Input bind:value={name} placeholder="播放清單名稱" autofocus />
	</form>
	{#snippet footer()}
		<Button variant="ghost" onclick={() => (dialogOpen = false)}>取消</Button>
		<Button variant="primary" type="submit" form="create-playlist" disabled={!name.trim() || creating}>
			建立
		</Button>
	{/snippet}
</Dialog>
