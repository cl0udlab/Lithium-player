<script lang="ts">
	import { untrack } from 'svelte'
	import { Search, Tv } from 'lucide-svelte'
	import { searchBangumi, type BangumiCandidate } from '$lib/video'
	import Button from '$lib/components/ui/Button.svelte'
	import Dialog from '$lib/components/ui/Dialog.svelte'
	import Input from '$lib/components/ui/Input.svelte'
	import Spinner from '$lib/components/ui/Spinner.svelte'

	let {
		open = $bindable(false),
		query: initialQuery = '',
		description = '選擇正確的 Bangumi 條目，會重新抓取標題、簡介和封面。',
		onselect
	}: {
		open?: boolean
		query?: string
		description?: string

		onselect: (candidate: BangumiCandidate) => Promise<boolean>
	} = $props()

	let query = $state('')
	let results = $state<BangumiCandidate[]>([])
	let searching = $state(false)
	let searched = $state(false)
	let applyingId = $state<number | null>(null)

	$effect(() => {
		if (!open) return
		untrack(() => {
			query = initialQuery
			results = []
			searched = false
			if (query.trim()) search()
		})
	})

	async function search(e?: SubmitEvent) {
		e?.preventDefault()
		if (!query.trim()) return
		searching = true
		try {
			results = await searchBangumi(query.trim())
			searched = true
		} finally {
			searching = false
		}
	}

	async function choose(candidate: BangumiCandidate) {
		applyingId = candidate.id
		try {
			if (await onselect(candidate)) open = false
		} finally {
			applyingId = null
		}
	}
</script>

<Dialog bind:open title="手動配對動畫" {description} class="w-[min(40rem,calc(100vw-2rem))]">
	<form class="flex gap-2" onsubmit={search}>
		<Input bind:value={query} icon={Search} placeholder="輸入動畫名稱" class="flex-1" />
		<Button type="submit" variant="primary" disabled={searching || !query.trim()}>搜尋</Button>
	</form>

	<div class="mt-4 min-h-40">
		{#if searching}
			<div class="grid h-40 place-items-center"><Spinner /></div>
		{:else if results.length}
			<ul class="flex flex-col gap-1">
				{#each results as candidate (candidate.id)}
					<li>
						<button
							class="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-line/5 disabled:opacity-50"
							disabled={applyingId !== null}
							onclick={() => choose(candidate)}
						>
							<div class="aspect-[3/4] w-12 shrink-0 overflow-hidden rounded-md bg-surface-3">
								{#if candidate.image}
									<img
										src={candidate.image}
										alt=""
										loading="lazy"
										referrerpolicy="no-referrer"
										class="h-full w-full object-cover"
									/>
								{:else}
									<Tv class="m-auto h-full w-1/2 text-fg-subtle" />
								{/if}
							</div>
							<div class="min-w-0 flex-1">
								<p class="truncate text-sm font-semibold">{candidate.name_cn || candidate.name}</p>
								{#if candidate.name_cn && candidate.name !== candidate.name_cn}
									<p class="truncate text-xs text-fg-muted">{candidate.name}</p>
								{/if}
								<p class="mt-0.5 text-[11px] text-fg-subtle">
									{candidate.air_date || '日期不明'} · Bangumi #{candidate.id}
								</p>
							</div>
							{#if applyingId === candidate.id}
								<Spinner class="h-4 w-4 shrink-0" />
							{/if}
						</button>
					</li>
				{/each}
			</ul>
		{:else if searched}
			<p class="py-12 text-center text-sm text-fg-muted">找不到符合的條目，換個名稱試試。</p>
		{/if}
	</div>
</Dialog>
