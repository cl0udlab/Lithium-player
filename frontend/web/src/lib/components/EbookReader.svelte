<script lang="ts">
	import { onMount } from 'svelte'
	import { ChevronLeft, ChevronRight } from 'lucide-svelte'
	import Button from '$lib/components/ui/Button.svelte'
	import Spinner from '$lib/components/ui/Spinner.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'

	let { file }: { file: File } = $props()

	type TocItem = { label: string; href: string; subitems?: TocItem[] | null }

	let container: HTMLDivElement
	let view: any = null
	let loading = $state(true)
	let error = $state('')
	let fraction = $state(0)
	let toc = $state<{ label: string; href: string; depth: number }[]>([])
	let currentHref = $state('')

	function flattenToc(items: TocItem[] | null | undefined, depth = 0): typeof toc {
		return (items ?? []).flatMap((item) => [
			{ label: item.label?.trim() || '(無標題)', href: item.href, depth },
			...flattenToc(item.subitems, depth + 1)
		])
	}

	function bookCSS(color: string) {
		return `
			html { color-scheme: light dark; color: ${color}; }
			a:link { color: inherit; }
			p, li, blockquote, dd { line-height: 1.7; text-align: justify; }
			pre { white-space: pre-wrap !important; }
			img, svg { max-width: 100%; height: auto; }
		`
	}

	function onKeydown(e: KeyboardEvent) {
		if (!view) return
		if (e.key === 'ArrowLeft') view.goLeft()
		else if (e.key === 'ArrowRight') view.goRight()
	}

	onMount(() => {
		let cancelled = false
		;(async () => {
			try {
				await import('foliate-js/view.js')
				if (cancelled) return
				view = document.createElement('foliate-view')
				view.style.cssText = 'display:block;width:100%;height:100%'
				container.append(view)
				await view.open(file)
				if (cancelled) return
				view.renderer.setAttribute('flow', 'paginated')
				view.renderer.setAttribute('max-inline-size', '720px')
				view.renderer.setStyles?.(bookCSS(getComputedStyle(container).color))
				toc = flattenToc(view.book.toc)
				view.addEventListener('relocate', (e: CustomEvent) => {
					fraction = e.detail.fraction ?? 0
					currentHref = e.detail.tocItem?.href ?? ''
				})

				view.addEventListener('load', (e: CustomEvent) =>
					e.detail.doc.addEventListener('keydown', onKeydown)
				)
				await view.init({ showTextStart: true })
			} catch (e) {
				console.error(e)
				error = (e as Error).message || '無法開啟這本書'
			} finally {
				loading = false
			}
		})()
		return () => {
			cancelled = true
			view?.close?.()
			view?.remove()
			view = null
		}
	})
</script>

<svelte:window onkeydown={onKeydown} />

<div class="flex h-full min-h-[70vh] flex-col">
	{#if toc.length}
		<select
			class="mb-3 h-9 w-full rounded-lg border border-line/10 bg-surface-2 px-3 text-sm text-fg outline-hidden focus:border-accent/60"
			aria-label="目錄"
			value={currentHref}
			onchange={(e) => view?.goTo(e.currentTarget.value)}
		>
			{#if !toc.some((item) => item.href === currentHref)}
				<option value={currentHref} disabled>目錄</option>
			{/if}
			{#each toc as item, i (i)}
				<option value={item.href}>{'　'.repeat(item.depth)}{item.label}</option>
			{/each}
		</select>
	{/if}

	<div class="relative min-h-0 flex-1">
		<div bind:this={container} class="h-full w-full text-fg"></div>
		{#if loading}
			<div class="absolute inset-0 grid place-items-center bg-surface">
				<Spinner class="h-6 w-6" />
			</div>
		{:else if error}
			<div class="absolute inset-0 grid place-items-center bg-surface">
				<StatusMessage kind="error" title="無法開啟這本書" message={error} />
			</div>
		{/if}
	</div>

	{#if !loading && !error}
		<div class="mt-3 flex items-center gap-3">
			<Button size="icon-sm" variant="ghost" onclick={() => view?.goLeft()} aria-label="上一頁">
				<ChevronLeft class="h-4 w-4" />
			</Button>
			<input
				type="range"
				min="0"
				max="1"
				step="0.001"
				value={fraction}
				oninput={(e) => view?.goToFraction(parseFloat(e.currentTarget.value))}
				class="flex-1 accent-accent"
				aria-label="閱讀進度"
			/>
			<span class="w-12 text-right text-xs text-fg-muted tabular-nums">
				{Math.round(fraction * 100)}%
			</span>
			<Button size="icon-sm" variant="ghost" onclick={() => view?.goRight()} aria-label="下一頁">
				<ChevronRight class="h-4 w-4" />
			</Button>
		</div>
	{/if}
</div>
