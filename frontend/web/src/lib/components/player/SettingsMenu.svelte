<script lang="ts">
	import { onMount } from 'svelte'
	import { Upload, Trash2, Check, Film } from 'lucide-svelte'
	import { apiFetch } from '$lib/api'
	import Slider from '$lib/components/ui/Slider.svelte'
	import Spinner from '$lib/components/ui/Spinner.svelte'
	import Switch from '$lib/components/ui/Switch.svelte'
	import {
		playerSettings,
		guessMediaType,
		resolveBackgroundUrl,
		type DisplayMode
	} from '$lib/stores/playerSettings'

	interface BackgroundFile {
		id: string
		type: 'image' | 'video'
		size: number
	}

	let backgrounds = $state<BackgroundFile[]>([])
	let uploading = $state(false)
	let error = $state('')
	let urlInput = $state('')
	let fileInput = $state<HTMLInputElement>()

	const bg = $derived($playerSettings.background)

	const uploadedPath = (id: string) => `/background/${id}`

	async function loadBackgrounds() {
		try {
			const response = await apiFetch('/background')
			if (response.ok) backgrounds = await response.json()
		} catch (e) {
			console.error(e)
		}
	}

	onMount(loadBackgrounds)

	function setMode(mode: DisplayMode) {
		playerSettings.patch({ mode })
	}

	function useCover() {
		playerSettings.patch({ background: { ...bg, source: 'cover' } })
	}

	function useBackground(url: string, type: 'image' | 'video') {
		playerSettings.patch({ background: { source: 'custom', url, type } })
	}

	function selectCustom() {
		if (bg.url) useBackground(bg.url, bg.type)
		else if (backgrounds[0]) pickUploaded(backgrounds[0])
		else playerSettings.patch({ background: { ...bg, source: 'custom' } })
	}

	function pickUploaded(file: BackgroundFile) {
		useBackground(uploadedPath(file.id), file.type)
	}

	function applyUrl() {
		const url = urlInput.trim()
		if (!/^https?:\/\//.test(url)) {
			error = '請輸入 http(s) 開頭的網址'
			return
		}
		error = ''
		useBackground(url, guessMediaType(url))
		urlInput = ''
	}

	async function upload(e: Event) {
		const file = (e.currentTarget as HTMLInputElement).files?.[0]
		if (!file) return
		uploading = true
		error = ''
		try {
			const form = new FormData()
			form.append('file', file)
			const response = await apiFetch('/background', { method: 'POST', body: form })
			if (!response.ok) {
				const body = await response.json().catch(() => null)
				error = body?.detail ?? `上傳失敗 (${response.status})`
				return
			}
			const saved: BackgroundFile = await response.json()
			backgrounds = [saved, ...backgrounds]
			pickUploaded(saved)
		} catch {
			error = '無法連接到伺服器'
		} finally {
			uploading = false
			if (fileInput) fileInput.value = ''
		}
	}

	async function remove(file: BackgroundFile) {
		const response = await apiFetch(`/background/${file.id}`, { method: 'DELETE' })
		if (!response.ok) return
		backgrounds = backgrounds.filter((b) => b.id !== file.id)
		if (bg.url === uploadedPath(file.id)) useCover()
	}

	const segment = (active: boolean) =>
		`flex-1 rounded-md py-1.5 transition-colors ${active ? 'bg-white text-black' : 'text-white/70 hover:bg-white/10'}`
</script>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div
	class="absolute bottom-24 right-6 z-10 max-h-[calc(100vh-8rem)] w-80 overflow-y-auto rounded-2xl border border-white/10 bg-neutral-900/85 p-4 text-sm text-white shadow-2xl backdrop-blur-xl"
	onclick={(e) => e.stopPropagation()}
>
	<p class="mb-2 text-xs font-semibold uppercase tracking-wider text-white/40">顯示模式</p>
	<div class="flex gap-1 rounded-lg bg-white/5 p-1">
		<button class={segment($playerSettings.mode === 'lyrics')} onclick={() => setMode('lyrics')}>
			歌詞
		</button>
		<button class={segment($playerSettings.mode === 'art')} onclick={() => setMode('art')}>
			封面
		</button>
	</div>

	<div
		class="mt-3 flex items-center justify-between rounded-lg px-1 py-2 {$playerSettings.mode === 'art'
			? ''
			: 'opacity-40'}"
	>
		<span>封面模式顯示歌詞</span>
		<Switch
			label="封面模式顯示歌詞"
			bind:checked={() => $playerSettings.artLyrics, (artLyrics) => playerSettings.patch({ artLyrics })}
		/>
	</div>

	<p class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wider text-white/40">背景</p>
	<div class="flex gap-1 rounded-lg bg-white/5 p-1">
		<button class={segment(bg.source === 'cover')} onclick={useCover}>專輯封面</button>
		<button class={segment(bg.source === 'custom')} onclick={selectCustom}>自訂</button>
	</div>

	{#if bg.source === 'custom'}
		<div class="mt-3 grid grid-cols-3 gap-2">
			{#each backgrounds as file (file.id)}
				{@const selected = bg.url === uploadedPath(file.id)}
				<div class="group relative aspect-video overflow-hidden rounded-md bg-white/5">
					<button class="h-full w-full" onclick={() => pickUploaded(file)} title={file.id}>
						{#if file.type === 'video'}
							<video
								src={resolveBackgroundUrl(uploadedPath(file.id))}
								muted
								preload="metadata"
								class="h-full w-full object-cover"
							></video>
							<Film class="absolute bottom-1 left-1 h-3 w-3 drop-shadow-sm" />
						{:else}
							<img
								src={resolveBackgroundUrl(uploadedPath(file.id))}
								alt=""
								class="h-full w-full object-cover"
							/>
						{/if}
					</button>
					{#if selected}
						<div class="pointer-events-none absolute inset-0 grid place-items-center ring-2 ring-inset ring-white">
							<Check class="h-5 w-5 drop-shadow-sm" />
						</div>
					{/if}
					<button
						class="absolute right-1 top-1 hidden rounded-sm bg-black/60 p-1 hover:bg-red-600 group-hover:block"
						onclick={() => remove(file)}
						aria-label="刪除背景"
					>
						<Trash2 class="h-3 w-3" />
					</button>
				</div>
			{/each}
			<button
				class="grid aspect-video place-items-center rounded-md border border-dashed border-white/25 text-white/60 hover:border-white/60 hover:text-white"
				onclick={() => fileInput?.click()}
				disabled={uploading}
				title="上傳圖片或影片"
			>
				{#if uploading}
					<Spinner class="h-4 w-4" />
				{:else}
					<Upload class="h-4 w-4" />
				{/if}
			</button>
		</div>
		<input
			bind:this={fileInput}
			type="file"
			accept="image/*,video/mp4,video/webm"
			class="hidden"
			onchange={upload}
		/>

		<div class="mt-3 flex gap-2">
			<input
				type="url"
				placeholder="或貼上圖片 / 影片網址"
				class="min-w-0 flex-1 rounded-md border border-white/15 bg-white/5 px-2 py-1.5 text-xs outline-hidden focus:border-white/40"
				bind:value={urlInput}
				onkeydown={(e) => e.key === 'Enter' && applyUrl()}
			/>
			<button class="rounded-md bg-white/10 px-3 text-xs hover:bg-white/20" onclick={applyUrl}>
				套用
			</button>
		</div>
		{#if bg.url && !bg.url.startsWith('/background/')}
			<p class="mt-2 truncate text-xs text-white/40" title={bg.url}>目前: {bg.url}</p>
		{/if}
	{/if}

	{#if error}
		<p class="mt-2 text-xs text-red-400">{error}</p>
	{/if}

	<div class="mt-4 flex items-center justify-between">
		<span class="text-xs font-semibold uppercase tracking-wider text-white/40">背景亮度</span>
		<span class="font-mono text-xs text-white/50">{Math.round($playerSettings.brightness * 100)}%</span>
	</div>
	<Slider
		class="mt-2"
		label="背景亮度"
		min={0.2}
		max={1}
		step={0.05}
		value={$playerSettings.brightness}
		onchange={(brightness) => playerSettings.patch({ brightness })}
	/>

	<p class="mt-4 border-t border-white/10 pt-3 text-[11px] leading-relaxed text-white/35">
		Space 播放/暫停 · ←/→ 快轉 · L 切換模式 · F 全螢幕 · Esc 收起
	</p>
</div>
