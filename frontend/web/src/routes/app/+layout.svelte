<script lang="ts">
	import { setContext, type Snippet } from 'svelte'
	import type { LayoutData } from './$types'
	import { playerState } from '$lib/stores/player'
	import { playerSettings } from '$lib/stores/playerSettings'
	import { goto } from '$app/navigation'
	import { page } from '$app/state'
	import Cookies from 'js-cookie'
	import type { PlayableTrack, Video } from '$lib/types'
	import Sidebar from '$lib/components/shell/Sidebar.svelte'
	import Topbar from '$lib/components/shell/Topbar.svelte'
	import MiniPlayer from '$lib/components/shell/MiniPlayer.svelte'
	import FullscreenPlayer from '$lib/components/FullscreenPlayer.svelte'

	let { data, children }: { data: LayoutData; children: Snippet } = $props()

	let player = $state<HTMLAudioElement | null>(null)
	let sidebarExpanded = $state(data.isExpanded)

	function stopMusic() {
		playerState.stop()
	}

	function playMusiclist(musiclist: PlayableTrack[], startIndex = 0) {
		playerState.setPlayer(player as HTMLAudioElement)
		playerState.playMusiclist(musiclist, startIndex)
	}

	function playMusic(track: PlayableTrack) {
		playerState.setPlayer(player as HTMLAudioElement)
		playerState.playMusic(track)
	}

	function playVideo(video: Video) {
		stopMusic()
		goto(`/app/videoplay?id=${video.id}`)
	}

	function toggleSidebar() {
		sidebarExpanded = !sidebarExpanded
		Cookies.set('isExpanded', String(sidebarExpanded))
	}

	function togglePlayer() {
		playerState.toggleExpanded()
		if ($playerState.isExpanded) {
			goto('/app/play')
		} else {
			history.back()
		}
	}

	setContext('playMusic', playMusic)
	setContext('playVideo', playVideo)
	setContext('stopMusic', stopMusic)
	setContext('playMusiclist', playMusiclist)

	$effect(() => {
		if (page.route.id === '/app/play') {
			playerState.setExpanded(true)
		} else if ($playerState.isExpanded) {
			playerState.setExpanded(false)
		}
	})

	$effect(() => {
		if (player) player.volume = $playerSettings.volume
	})
</script>

<div class="min-h-screen">
	<Sidebar expanded={sidebarExpanded} onToggle={toggleSidebar} />

	<div class="transition-[padding] duration-200 {sidebarExpanded ? 'pl-60' : 'pl-[72px]'}">
		<Topbar />
		<main class="px-6 pb-32 pt-6 md:px-8">
			{@render children()}
		</main>
	</div>

	<audio bind:this={player} class="hidden" crossorigin="anonymous"></audio>

	{#if $playerState.isExpanded && $playerState.currentTrack}
		<FullscreenPlayer {player} onClose={togglePlayer} />
	{/if}

	{#if $playerState.currentTrack && !$playerState.isExpanded}
		<div
			class="fixed bottom-3 right-3 z-40 animate-slide-up transition-[left] duration-200 {sidebarExpanded
				? 'left-[252px]'
				: 'left-[84px]'}"
		>
			<MiniPlayer {player} onExpand={togglePlayer} />
		</div>
	{/if}
</div>
