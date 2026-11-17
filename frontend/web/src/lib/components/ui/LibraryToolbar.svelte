<script lang="ts">
	import { goto } from '$app/navigation'
	import Button from './Button.svelte'
	import Input from './Input.svelte'
	let {
		path,
		total,
		page,
		size,
		q,
		cached = false,
		offlineFilter = false
	}: {
		path: string
		total: number
		page: number
		size: number
		q: string
		cached?: boolean
		offlineFilter?: boolean
	} = $props()
	let search = $state('')
	let offline = $state(false)
	$effect(() => {
		search = q
		offline = cached
	})
	const pages = $derived(Math.max(1, Math.ceil(total / size)))
	function link(next: number, term = q, onlyCached = cached) {
		const params = new URLSearchParams({ page: String(next) })
		if (term.trim()) params.set('q', term.trim())
		if (onlyCached) params.set('cached', 'true')
		return `${path}?${params}`
	}
</script>

<div class="my-4 flex flex-wrap items-center justify-between gap-3">
	<form
		class="flex flex-wrap items-center gap-2"
		onsubmit={(event) => {
			event.preventDefault()
			void goto(link(1, search, offline))
		}}
	>
		<Input
			type="search"
			aria-label="搜尋媒體庫"
			placeholder="搜尋標題、演出者、專輯"
			bind:value={search}
		/>
		{#if offlineFilter}<label class="flex items-center gap-2 text-sm text-fg-muted"
				><input type="checkbox" bind:checked={offline} />僅顯示已快取</label
			>{/if}
		<Button type="submit">搜尋</Button>
	</form>
	<nav class="flex items-center gap-3" aria-label="媒體庫分頁">
		<Button href={page > 1 ? link(page - 1) : undefined} disabled={page <= 1}>上一頁</Button>
		<span class="text-sm text-fg-muted">{page} / {pages} · 共 {total} 筆</span>
		<Button href={page < pages ? link(page + 1) : undefined} disabled={page >= pages}>下一頁</Button
		>
	</nav>
</div>
