<script lang="ts">
	import { page } from '$app/state'
	import {
		House,
		Music,
		Disc3,
		ListMusic,
		Clapperboard,
		Tv,
		FolderOpen,
		Settings,
		PanelLeft
	} from 'lucide-svelte'
	import Tooltip from '$lib/components/ui/Tooltip.svelte'

	let { expanded, onToggle }: { expanded: boolean; onToggle: () => void } = $props()

	const sections = [
		{
			title: '音樂',
			items: [
				{ href: '/app', label: '首頁', icon: House },
				{ href: '/app/music', label: '歌曲', icon: Music },
				{ href: '/app/albums', label: '專輯', icon: Disc3 },
				{ href: '/app/playlist', label: '播放清單', icon: ListMusic }
			]
		},
		{
			title: '影音',
			items: [
				{ href: '/app/video', label: '影片', icon: Clapperboard },
				{ href: '/app/anime', label: '動畫', icon: Tv },
				{ href: '/app/file', label: '檔案', icon: FolderOpen }
			]
		}
	]

	function isActive(href: string) {
		const path = page.url.pathname
		return href === '/app' ? path === '/app' : path.startsWith(href)
	}
</script>

{#snippet navItem(item: { href: string; label: string; icon: typeof House })}
	{@const active = isActive(item.href)}
	<Tooltip text={item.label} disabled={expanded}>
		{#snippet children(trigger)}
			<a
				{...trigger}
				href={item.href}
				aria-current={active ? 'page' : undefined}
				class="relative flex h-10 items-center gap-3 rounded-lg text-sm font-medium transition-colors {expanded
					? 'px-3'
					: 'justify-center'} {active
					? 'bg-line/8 text-fg'
					: 'text-fg-muted hover:bg-line/5 hover:text-fg'}"
			>
				{#if active}
					<span class="absolute -left-3 top-2 bottom-2 w-1 rounded-r-full bg-accent"></span>
				{/if}
				<item.icon class="h-[18px] w-[18px] shrink-0 {active ? 'text-accent' : ''}" />
				{#if expanded}
					<span class="truncate">{item.label}</span>
				{/if}
			</a>
		{/snippet}
	</Tooltip>
{/snippet}

<aside
	class="fixed inset-y-0 left-0 z-40 flex flex-col border-r border-line/5 bg-bg px-3 pb-4 transition-[width] duration-200 {expanded
		? 'w-60'
		: 'w-[72px]'}"
	aria-label="側邊欄"
>
	<div class="flex h-16 items-center {expanded ? 'justify-between pl-2' : 'justify-center'}">
		{#if expanded}
			<a href="/app" class="flex items-center gap-2.5">
				<img src="/Lithium.png" alt="" class="h-7 w-7" />
				<span class="text-lg font-bold tracking-tight">Lithium</span>
			</a>
		{/if}
		<button
			class="grid h-9 w-9 place-items-center rounded-lg text-fg-muted transition-colors hover:bg-line/5 hover:text-fg"
			onclick={onToggle}
			aria-label={expanded ? '收合側邊欄' : '展開側邊欄'}
		>
			<PanelLeft class="h-[18px] w-[18px]" />
		</button>
	</div>

	<nav class="mt-2 flex flex-1 flex-col gap-6 overflow-y-auto no-scrollbar">
		{#each sections as section (section.title)}
			<div class="flex flex-col gap-1">
				{#if expanded}
					<p class="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-fg-subtle">
						{section.title}
					</p>
				{:else}
					<div class="mx-auto mb-1 h-px w-6 bg-line/10"></div>
				{/if}
				{#each section.items as item (item.href)}
					{@render navItem(item)}
				{/each}
			</div>
		{/each}
	</nav>

	{@render navItem({ href: '/app/setting', label: '設定', icon: Settings })}
</aside>
