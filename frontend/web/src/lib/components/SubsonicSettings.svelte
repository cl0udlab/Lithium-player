<script lang="ts">
	import { onMount } from 'svelte'
	import { apiFetch } from '$lib/api'
	import { toast } from '$lib/stores/toast.svelte'
	import Button from '$lib/components/ui/Button.svelte'
	import Input from '$lib/components/ui/Input.svelte'
	let url = $state(''),
		username = $state(''),
		password = $state('')
	let busy = $state(false),
		message = $state('')
	async function request(path: string, method = 'GET', body?: unknown) {
		const response = await apiFetch(`/subsonic${path}`, {
			method,
			...(body
				? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
				: {})
		})
		const data = await response.json()
		if (!response.ok)
			throw new Error(typeof data.detail === 'string' ? data.detail : '請檢查連線設定')
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
	onMount(() => {
		void run(async () => {
			const connection = await request('/connection')
			if (connection) {
				url = connection.url
				username = connection.username
				message = '已設定連線'
			}
		})
	})
</script>

<section class="mb-6 flex max-w-3xl flex-col gap-3 rounded-2xl border border-line/5 bg-surface p-6">
	<h2 class="font-semibold">Subsonic 音樂來源</h2>
	<p class="text-sm text-fg-muted">
		管理員可設定 Subsonic / Navidrome 相容伺服器。同步後會顯示在歌曲與專輯中；播放前會完整快取歌曲。
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

						message = `已同步 ${result.total} 首歌曲，可前往歌曲與專輯瀏覽`
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
	<div class="flex gap-3 text-sm text-accent">
		<a href="/app/music">瀏覽歌曲</a><a href="/app/albums">瀏覽專輯</a>
	</div>
</section>
