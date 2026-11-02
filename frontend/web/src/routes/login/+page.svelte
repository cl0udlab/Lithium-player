<script lang="ts">
	import { goto } from '$app/navigation'
	import { User, Lock, CircleAlert } from 'lucide-svelte'
	import Cookies from 'js-cookie'
	import { APIUrl } from '$lib/api'
	import Button from '$lib/components/ui/Button.svelte'
	import Input from '$lib/components/ui/Input.svelte'
	import Spinner from '$lib/components/ui/Spinner.svelte'

	interface LoginResponse {
		access_token: string
		refresh_token: string
		token_type: string
	}

	let username = $state('')
	let password = $state('')
	let error = $state('')
	let loading = $state(false)

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault()
		if (!username || !password) {
			error = '請填寫所有欄位'
			return
		}
		loading = true
		error = ''
		try {
			const response = await fetch(`${APIUrl}/auth/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password })
			})
			if (!response.ok) {
				const data = await response.json()
				error = data.detail === 'Invalid credentials' ? '帳號或密碼錯誤' : data.detail || '登入失敗'
				return
			}
			const data: LoginResponse = await response.json()
			Cookies.set('access_token', data.access_token)
			Cookies.set('refresh_token', data.refresh_token)
			await goto('/app')
		} catch {
			error = '伺服器連接失敗'
		} finally {
			loading = false
		}
	}
</script>

<svelte:head>
	<title>登入 - Lithium Player</title>
</svelte:head>

<div class="grid min-h-screen place-items-center p-4">
	<div class="w-full max-w-sm">
		<div class="mb-8 flex flex-col items-center text-center">
			<img src="/Lithium.png" alt="" class="mb-4 h-14 w-14" />
			<h1 class="text-2xl font-bold tracking-tight">Lithium Player</h1>
			<p class="mt-1 text-sm text-fg-muted">歡迎回來, 請登入你的帳號</p>
		</div>

		<form
			onsubmit={handleSubmit}
			class="flex flex-col gap-4 rounded-2xl border border-line/10 bg-surface p-6"
		>
			{#if error}
				<div role="alert" class="flex items-center gap-2 rounded-lg bg-danger/10 px-3 py-2.5 text-sm text-danger">
					<CircleAlert class="h-4 w-4 shrink-0" />
					{error}
				</div>
			{/if}
			<label class="flex flex-col gap-1.5">
				<span class="text-xs font-medium text-fg-muted">使用者名稱</span>
				<Input bind:value={username} icon={User} autocomplete="username" placeholder="使用者名稱" />
			</label>
			<label class="flex flex-col gap-1.5">
				<span class="text-xs font-medium text-fg-muted">密碼</span>
				<Input
					type="password"
					bind:value={password}
					icon={Lock}
					autocomplete="current-password"
					placeholder="密碼"
				/>
			</label>
			<Button variant="primary" size="lg" type="submit" class="mt-2 w-full" disabled={loading}>
				{#if loading}<Spinner class="h-4 w-4" />{/if}
				登入
			</Button>
		</form>
	</div>
</div>
