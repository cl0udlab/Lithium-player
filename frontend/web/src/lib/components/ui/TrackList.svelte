<script lang="ts">
	import type { Snippet } from 'svelte'
	import { Play, Music, AudioLines } from 'lucide-svelte'
	import { coverUrl } from '$lib/api'
	import { playerState } from '$lib/stores/player'
	import { formatDuration } from '$lib/utils/library'
	import { trackKey, type PlayableTrack } from '$lib/types'

	let {
		tracks,
		onplay,
		showCover = true,
		showAlbum = true,
		numbered = true,
		actions
	}: {
		tracks: PlayableTrack[]
		onplay: (index: number) => void
		showCover?: boolean
		showAlbum?: boolean
		numbered?: boolean
		actions?: Snippet<[PlayableTrack, number]>
	} = $props()

	const currentKey = $derived(
		$playerState.currentTrack && 'artist' in $playerState.currentTrack
			? trackKey($playerState.currentTrack as PlayableTrack)
			: null
	)
</script>

<div class="flex flex-col">
	<div
		class="grid grid-cols-[2.5rem_minmax(0,1fr)_4rem] items-center gap-4 border-b border-line/5 px-3 pb-2 text-xs font-medium tracking-wider text-fg-subtle uppercase {showAlbum
			? 'md:grid-cols-[2.5rem_minmax(0,2fr)_minmax(0,1fr)_4rem]'
			: ''}"
	>
		<span class="text-center">#</span>
		<span>標題</span>
		{#if showAlbum}<span class="hidden md:block">專輯</span>{/if}
		<span class="text-right">時長</span>
	</div>
	{#each tracks as track, i (trackKey(track))}
		{@const active = currentKey === trackKey(track)}
		{@const cover = showCover ? coverUrl(track.cover_art, 96) : null}
		<div
			class="group grid grid-cols-[2.5rem_minmax(0,1fr)_4rem] items-center gap-4 rounded-lg px-3 py-2 transition-colors hover:bg-line/5 {showAlbum
				? 'md:grid-cols-[2.5rem_minmax(0,2fr)_minmax(0,1fr)_4rem]'
				: ''}"
			ondblclick={() => onplay(i)}
			role="row"
			tabindex="-1"
		>
			<div class="relative grid h-8 place-items-center text-sm text-fg-subtle">
				{#if active}
					<AudioLines class="h-4 w-4 text-accent group-hover:hidden" />
				{:else if numbered}
					<span class="tabular-nums group-hover:hidden">{i + 1}</span>
				{/if}
				<button
					class="absolute inset-0 hidden place-items-center text-fg group-hover:grid"
					onclick={() => onplay(i)}
					aria-label="播放 {track.title}"
				>
					<Play class="h-4 w-4" fill="currentColor" />
				</button>
			</div>
			<div class="flex min-w-0 items-center gap-3">
				{#if showCover}
					<div class="h-10 w-10 shrink-0 overflow-hidden rounded-md bg-surface-3">
						{#if cover}
							<img
								src={cover}
								alt=""
								loading="lazy"
								referrerpolicy="no-referrer"
								class="h-full w-full object-cover"
							/>
						{:else}
							<Music class="m-auto h-full w-4 text-fg-subtle" />
						{/if}
					</div>
				{/if}
				<div class="min-w-0">
					<p class="truncate text-sm font-medium {active ? 'text-accent' : ''}">{track.title}</p>
					<p class="truncate text-xs text-fg-muted">{track.artist}</p>
				</div>
			</div>
			{#if showAlbum}
				<p class="hidden truncate text-sm text-fg-muted md:block">
					{('album' in track && track.album) || ''}
				</p>
			{/if}
			<div class="flex items-center justify-end gap-1 text-sm text-fg-subtle tabular-nums">
				{#if actions}
					<span class="opacity-0 transition-opacity group-hover:opacity-100">
						{@render actions(track, i)}
					</span>
				{/if}
				<span>{formatDuration((track as any).duration ?? 0)}</span>
			</div>
		</div>
	{/each}
</div>
