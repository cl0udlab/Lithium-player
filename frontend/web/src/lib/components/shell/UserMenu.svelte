<script lang="ts">
	import { onMount } from 'svelte'
	import { goto } from '$app/navigation'
	import { Popover } from 'melt/builders'
	import { LogOut, Settings } from 'lucide-svelte'
	import Cookies from 'js-cookie'
	import { apiFetch } from '$lib/api'

	let user = $state<{ username: string; role: string } | null>(null)

	const popover = new Popover({
		floatingConfig: { computePosition: { placement: 'bottom-end' }, offset: { mainAxis: 8 } }
	})

	onMount(async () => {
		const response = await apiFetch('/user/me')
		if (response.ok) user = await response.json()
	})

	function logout() {
		Cookies.remove('access_token')
		Cookies.remove('refresh_token')
		goto('/login')
	}
</script>

<button
	{...popover.trigger}
	class="transition-transforms grid h-9 w-9 place-items-center rounded-full border border-lime-50/20 text-sm font-bold text-white uppercase"
	aria-label="使用者選單"
>
	{user?.username.charAt(0) ?? '?'}
</button>

<div
	{...popover.content}
	class="w-56 rounded-xl border border-line/10 bg-surface-2 p-1.5 shadow-lg"
>
	<div class="px-3 py-2">
		<p class="truncate text-sm font-semibold">{user?.username ?? '未登入'}</p>
		<p class="text-xs text-fg-subtle">{user?.role === 'admin' ? '管理員' : '使用者'}</p>
	</div>
	<div class="my-1 h-px bg-line/8"></div>
	<a
		href="/app/setting"
		onclick={() => (popover.open = false)}
		class="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-fg-muted hover:bg-line/5 hover:text-fg"
	>
		<Settings class="h-4 w-4" /> 設定
	</a>
	<button
		onclick={logout}
		class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-fg-muted hover:bg-danger/10 hover:text-danger"
	>
		<LogOut class="h-4 w-4" /> 登出
	</button>
</div>
