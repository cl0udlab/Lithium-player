<script lang="ts">
	import { getContext, tick } from 'svelte'
	import { goto } from '$app/navigation'
	import { Combobox } from 'melt/builders'
	import { Search, Music, Radio, Disc3, Clapperboard } from 'lucide-svelte'
	import { apiFetch } from '$lib/api'
	import Spinner from '$lib/components/ui/Spinner.svelte'
	import type { MusicTrack, PlayableTrack, StreamTrack } from '$lib/types'

	type Kind = 'music' | 'stream' | 'album' | 'video'
	interface Result {
		key: string
		kind: Kind
		id: number
		title: string
		subtitle?: string
	}

	const playMusic = getContext<(track: PlayableTrack) => void>('playMusic')
	const groups: { kind: Kind; label: string; icon: typeof Music }[] = [
		{ kind: 'music', label: '歌曲', icon: Music },
		{ kind: 'stream', label: '網路音訊', icon: Radio },
		{ kind: 'album', label: '專輯', icon: Disc3 },
		{ kind: 'video', label: '影片', icon: Clapperboard }
	]

	let query = $state('')
	let results = $state<Result[]>([])
	let loading = $state(false)
	let timer: ReturnType<typeof setTimeout>
	let requestId = 0

	const combobox = new Combobox<string>({
		inputValue: () => query,
		onInputValueChange: (value) => {
			query = value
			clearTimeout(timer)
			timer = setTimeout(() => search(value), 250)
		},
		floatingConfig: { computePosition: { placement: 'bottom-start' }, offset: { mainAxis: 6 } },
		sameWidth: true
	})

	async function search(value: string) {
		const name = value.trim()
		if (!name) {
			results = []
			return
		}
		const id = ++requestId
		loading = true
		try {
			const q = encodeURIComponent(name)
			const [all, music] = await Promise.all([
				apiFetch(`/file/search?name=${q}`).then((r) => (r.ok ? r.json() : [])),
				apiFetch(`/file/searchmusic?name=${q}`).then((r) =>
					r.ok ? r.json() : { musics: [], stream_tracks: [] }
				)
			])
			if (id !== requestId) return
			results = [
				...music.musics.map((m: any) => ({ kind: 'music', id: m.id, title: m.title, subtitle: m.artist })),
				...music.stream_tracks.map((s: any) => ({ kind: 'stream', id: s.id, title: s.title, subtitle: s.artist })),
				...all
					.filter((r: any) => r.type === 'album' || r.type === 'video')
					.map((r: any) => ({ kind: r.type, id: r.id, title: r.title }))
			]
				.slice(0, 30)
				.map((r) => ({ ...r, key: `${r.kind}-${r.id}` }))
			// Melt 只在輸入當下 highlight 第一個選項, 結果是非同步回來的, 要自己補;
			// 沒有 highlight 時方向鍵也沒反應 (findNext 找不到目前項目)
			await tick()
			combobox.highlightFirst()
		} finally {
			if (id === requestId) loading = false
		}
	}

	async function choose(result: Result) {
		query = ''
		results = []
		combobox.open = false
		switch (result.kind) {
			case 'album':
				return goto(`/app/albums/${result.id}`)
			case 'video':
				return goto(`/app/videoplay?id=${result.id}`)
			case 'music': {
				const response = await apiFetch(`/file/music?track_id=${result.id}`)
				if (response.ok) playMusic({ ...((await response.json()) as MusicTrack), kind: 'music' })
				return
			}
			case 'stream': {
				const response = await apiFetch('/file/streamtracks')
				const track = response.ok
					? ((await response.json()) as StreamTrack[]).find((t) => t.id === result.id)
					: null
				if (track) playMusic({ ...track, kind: 'stream' })
				return
			}
		}
	}

	// 下拉選單只在有輸入時顯示
	$effect(() => {
		if (!query.trim() && combobox.open) tick().then(() => (combobox.open = false))
	})
</script>

<div class="relative w-full max-w-md">
	<Search class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-fg-subtle" />
	<input
		{...combobox.input}
		type="search"
		placeholder="搜尋歌曲、專輯、影片…"
		class="h-10 w-full rounded-full border border-line/10 bg-surface-2/80 pl-10 pr-10 text-sm outline-hidden transition-colors placeholder:text-fg-subtle hover:border-line/20 focus:border-accent/50 focus:bg-surface-2"
	/>
	{#if loading}
		<Spinner class="absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-fg-subtle" />
	{/if}

	<div
		{...combobox.content}
		class="max-h-[min(28rem,70vh)] overflow-y-auto rounded-xl border border-line/10 bg-surface-2 p-1.5 shadow-lg"
	>
		{#if results.length === 0}
			<p class="px-3 py-6 text-center text-sm text-fg-subtle">
				{loading ? '搜尋中…' : '找不到結果'}
			</p>
		{/if}
		{#each groups as group (group.kind)}
			{@const items = results.filter((r) => r.kind === group.kind)}
			{#if items.length > 0}
				<p class="px-3 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-fg-subtle">
					{group.label}
				</p>
				{#each items as result (result.key)}
					<div
						{...combobox.getOption(result.key, result.title, () => choose(result))}
						class="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm data-highlighted:bg-line/10"
					>
						<group.icon class="h-4 w-4 shrink-0 text-fg-subtle" />
						<div class="min-w-0">
							<p class="truncate">{result.title}</p>
							{#if result.subtitle}
								<p class="truncate text-xs text-fg-muted">{result.subtitle}</p>
							{/if}
						</div>
					</div>
				{/each}
			{/if}
		{/each}
	</div>
</div>
