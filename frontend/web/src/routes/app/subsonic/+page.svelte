<script lang="ts">
	import { onMount, getContext } from 'svelte'
	import { apiFetch } from '$lib/api'
	import type { PlayableTrack, StreamTrack } from '$lib/types'
	import Button from '$lib/components/ui/Button.svelte'
	import Input from '$lib/components/ui/Input.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import TrackList from '$lib/components/ui/TrackList.svelte'
	import { toast } from '$lib/stores/toast.svelte'

	let url = $state('')
	let username = $state('')
	let password = $state('')
	let tracks = $state<(StreamTrack & { cached: boolean })[]>([])
	let busy = $state(false)
	let message = $state('')
	const play = getContext<(tracks: PlayableTrack[], start?: number) => void>('playMusiclist')

	async function request(path: string, method = 'GET', body?: unknown) {
		const response = await apiFetch(`/subsonic${path}`, {
			method,
			...(body
				? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
				: {})
		})
		const data = await response.json()
		if (!response.ok)
			throw new Error(typeof data.detail === 'string' ? data.detail : '請檢查設定與存取權限')
		return data
	}

	async function run(action: () => Promise<void>) {
		busy = true
		try {
			await action()
		} catch (error) {
			message = error instanceof Error ? error.message : '連線失敗'
			toast.error(message)
		} finally {
			busy = false
		}
	}

	async function refresh() {
		tracks = await request('/tracks')
	}

	onMount(() => {
		void run(async () => {
			await refresh()
			// Library browsing is available to all users; connection management requires admin.
			try {
				const connection = await request('/connection')
				if (connection) {
					url = connection.url
					username = connection.username
				}
			} catch {
				/* Non-admin users can still play the shared library. */
			}
		})
	})
</script>

<svelte:head><title>Subsonic - Lithium Player</title></svelte:head>

<PageHeader
	title="Subsonic"
	subtitle="{tracks.length} 首 · {tracks.filter((t) => t.cached).length} 首已快取"
/>

<section class="mb-6 flex max-w-3xl flex-col gap-3 rounded-2xl border border-line/5 bg-surface p-6">
	<h2 class="font-semibold">伺服器連線</h2>
	<p class="text-sm text-fg-muted">
		管理員可設定 Subsonic / Navidrome 相容伺服器。同步後可使用原有播放佇列；播放前會完整快取歌曲。
	</p>
	<form
		class="flex flex-col gap-3"
		onsubmit={(event) => {
			event.preventDefault()
			void run(async () => {
				await request('/connection', 'PUT', { url, username, password })
				password = ''
				message = '連線成功，請同步曲目'
			})
		}}
	>
		<Input
			aria-label="伺服器網址"
			placeholder="https://music.example.com"
			bind:value={url}
			required
		/>
		<Input
			aria-label="使用者名稱"
			placeholder="使用者名稱"
			bind:value={username}
			autocomplete="username"
			required
		/>
		<Input
			aria-label="密碼"
			placeholder="密碼"
			type="password"
			bind:value={password}
			autocomplete="current-password"
			required
		/>
		<div class="flex flex-wrap gap-2">
			<Button type="submit" variant="primary" disabled={busy}>儲存並測試連線</Button>
			<Button
				disabled={busy}
				onclick={() =>
					run(async () => {
						const result = await request('/sync', 'POST')
						await refresh()
						message = `已同步 ${result.total} 首歌曲`
					})}>同步曲目</Button
			>
			<Button
				disabled={busy}
				onclick={() =>
					run(async () => {
						const result = await request('/connection', 'DELETE')
						password = ''
						message = result.message
					})}>中斷連結</Button
			>
		</div>
	</form>
	<p class="text-sm text-fg-muted">
		已快取歌曲在遠端伺服器斷線或中斷連結後仍可播放。快取儲存在 Lithium 後端，瀏覽器仍需能連到
		Lithium。未快取歌曲需要恢復來源連線。
	</p>
	{#if message}<p role="status" class="text-sm text-accent">{message}</p>{/if}
	{#if busy}<p role="status" class="text-sm text-fg-muted">處理中…</p>{/if}
</section>

<div class="mb-4 flex flex-wrap gap-2">
	<Button disabled={busy || !tracks.length} onclick={() => play(tracks)}>播放全部</Button>
	<Button
		disabled={busy || !tracks.some((t) => t.cached)}
		onclick={() => play(tracks.filter((t) => t.cached))}>播放已快取歌曲</Button
	>
	<Button disabled={busy} onclick={() => run(refresh)}>重新整理</Button>
</div>

<TrackList {tracks} onplay={(index) => play(tracks, index)} showAlbum={false}>
	{#snippet actions(track)}
		<Button
			size="sm"
			disabled={busy || tracks.find((t) => t.id === track.id)?.cached}
			onclick={() =>
				run(async () => {
					await request(`/cache/${track.id}`, 'POST')
					await refresh()
					message = `已快取「${track.title}」`
				})}>{tracks.find((t) => t.id === track.id)?.cached ? '已快取' : '快取'}</Button
		>
	{/snippet}
</TrackList>
