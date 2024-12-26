<script lang="ts">
	import { goto } from '$app/navigation'
	import { Music } from 'lucide-svelte'
	import Cookies from 'js-cookie'

	interface LoginResponse {
		access_token: string
		refresh_token: string
		token_type: string
	}

	let username = ''
	let password = ''
	let error = ''

	async function handleSubmit() {
		if (!username || !password) {
			error = '請填寫所有欄位'
			return
		}

		try {
			const response = await fetch('http://localhost:8000/auth/login', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ username, password })
			})

			if (!response.ok) {
				const data = await response.json()
				error = data.detail || '登入失敗'
				return
			}

			const data: LoginResponse = await response.json()
			Cookies.set('access_token', data.access_token)
			Cookies.set('refresh_token', data.refresh_token)

			await goto('/app')
		} catch (err) {
			error = '伺服器連接失敗'
		}
	}
</script>

<svelte:head>
	<title>登入 - Lithium Player</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-base-200 p-4">
	<div class="hover:shadow-3xl card w-96 bg-base-100 shadow-2xl transition-shadow duration-300">
		<div class="card-body p-8">
			<div class="mb-8 flex flex-col items-center">
				<div class="mb-4 rounded-full bg-primary p-4 text-primary-content">
					<Music size={32} />
				</div>
				<h2 class="card-title text-3xl font-bold">Lithium Player</h2>
				<p class="mt-2 text-base-content/60">歡迎回來，請登入您的帳號</p>
			</div>

			{#if error}
				<div role="alert" class="alert alert-error">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6 shrink-0 stroke-current"
						fill="none"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<span>{error}</span>
				</div>
			{/if}

			<form on:submit|preventDefault={handleSubmit} class="form-control gap-4">
				<div class="form-control">
					<label class="label" for="username">
						<span class="label-text font-medium">用戶名</span>
					</label>
					<input
						id="username"
						type="text"
						bind:value={username}
						placeholder="請輸入用戶名"
						class="input input-bordered w-full transition-colors focus:input-primary"
					/>
				</div>

				<div class="form-control">
					<label class="label" for="password">
						<span class="label-text font-medium">密碼</span>
					</label>
					<input
						type="password"
						bind:value={password}
						placeholder="請輸入密碼"
						class="input input-bordered w-full transition-colors focus:input-primary"
					/>
				</div>

				<button type="submit" class="btn btn-primary mt-6 w-full"> 登入 </button>
			</form>
		</div>
	</div>
</div>
