<script lang="ts">
	import { setContext, type Snippet } from 'svelte'
	import type { LayoutData } from './$types'
	import { ChevronUp, ChevronLeft, ChevronRight, Play } from 'lucide-svelte'
	import { playerState } from '$lib/stores/player'
	import { goto } from '$app/navigation'
	import Navbar from '$lib/components/navbar.svelte'
	import Sidebar from '$lib/components/sidebar.svelte'
	import 'vidstack/player/styles/default/theme.css'
	import 'vidstack/player/styles/default/layouts/audio.css'
	import 'vidstack/player/styles/default/layouts/video.css'
	import 'vidstack/player'
	import 'vidstack/player/layouts/default'
	import 'vidstack/player/ui'

	import type { MediaPlayerElement } from 'vidstack/elements'
	import { browser } from '$app/environment'
	import { writable } from 'svelte/store'
	import { page } from '$app/stores'
	import type { MusicTrack, Video } from '$lib/types'
	import Cd from '$lib/image/cd.svelte'
	import Cookies from 'js-cookie'

	let player = $state<MediaPlayerElement | null>(null)

	let { data, children }: { data: LayoutData; children: Snippet } = $props()
	const isExpanded = writable<boolean>(data.isExpanded)

	function stopMusic() {
		playerState.stop()
	}

	function playMusiclist(musiclist: MusicTrack[]) {
		playerState.setPlayer(player as MediaPlayerElement)
		playerState.playMusiclist(musiclist)
	}

	function playMusic(track: MusicTrack) {
		playerState.setPlayer(player as MediaPlayerElement)
		playerState.playMusic(track)
	}

	function playVideo(video: Video) {
		stopMusic()
		goto(`/app/videoplay?id=${video.id}`)
	}

	function toggleSidebar() {
		isExpanded.update((value) => {
			const newValue = !value
			if (browser) {
				Cookies.set('isExpanded', String(newValue))
			}
			return newValue
		})
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
		if ($page.route.id === '/app/play') {
			playerState.setExpanded(true)
		} else if ($playerState.isExpanded) {
			playerState.setExpanded(false)
		}
	})
	function getCoverArtUrl(coverArt: string) {
		return `http://localhost:8000/file/image?image_id=${coverArt}&image_size=300`
	}
</script>

<div class="flex min-h-screen flex-col">
	<header class="fixed top-0 z-50 w-full">
		<Navbar onToggle={toggleSidebar} />
	</header>

	<div class="flex flex-1 pb-24 pt-16">
		<Sidebar isExpanded={$isExpanded} />

		<main class={`flex-1 p-4 transition-all ${$isExpanded ? 'pl-64' : 'pl-16'}`}>
			{@render children()}
		</main>

		<div
			class={`fixed left-0 right-0 flex w-full flex-col bg-base-100 transition-all duration-300 ${$playerState.isExpanded ? 'bottom0 top-20' : 'bottom-0 h-24'} ${$isExpanded ? 'pl-64' : 'pl-16'} ${$playerState.isPlaying ? '' : 'hidden'}`}
		>
			<div class="h-full w-full flex-1">
				<media-player
					class="h-full w-full"
					viewType="audio"
					streamType="on-demand"
					logLevel="debug"
					crossOrigin
					playsInline
					bind:this={player}
				>
					<media-provider></media-provider>
					{#if $playerState.isExpanded}
						<div class="h-[calc(100%-6rem)] p-4">
							<div class="grid h-full grid-cols-2 gap-8">
								<div class="rounded-lgp-4 w-72 bg-base-300 p-4 shadow-lg">
									{#if $playerState.currentTrack?.cover_art}
										<img
											src={getCoverArtUrl($playerState.currentTrack?.cover_art)}
											alt="Album art"
											class="mb-4 w-full rounded-lg bg-red-500 object-cover shadow-lg"
										/>
									{:else}
										<Cd class="mb-4 w-full" />
									{/if}
									<div class="mb-2 font-semibold">{$playerState.currentTrack?.title}</div>
									<div class="mb-3 text-sm text-gray-600">{$playerState.currentTrack?.artist}</div>
									<media-audio-layout> </media-audio-layout>
								</div>
								<div class="flex-1">
									<div class="space-y-2 text-lg">
										<div>placeholder1</div>
										<div class="bg-black py-1 text-white">placeholder2</div>
									</div>
								</div>
								<div class="flex flex-col">
									<button class="btn btn-ghost" onclick={togglePlayer}>
										<ChevronUp class="rotate-180" />
									</button>
								</div>
							</div>
						</div>
					{:else}
						<div class="grid h-24 w-full grid-cols-[auto_1fr_auto] items-center gap-4 px-4">
							<div class="flex items-center gap-4">
								{#if $playerState.currentTrack?.cover_art}
									<img
										src={getCoverArtUrl($playerState.currentTrack?.cover_art)}
										alt="Album art"
										class="h-16 w-16 rounded-lg object-cover"
									/>
								{:else}
									<Cd class="h-10 w-10" />
								{/if}
								<div>
									<h3 class="text-lg font-medium">{$playerState.currentTrack?.title}</h3>
									<p class="text-sm opacity-75">{$playerState.currentTrack?.artist}</p>
								</div>
							</div>
							<media-audio-layout></media-audio-layout>
							<button class="btn btn-ghost" onclick={togglePlayer}>
								<ChevronUp />
							</button>
						</div>
					{/if}
				</media-player>
			</div>
		</div>
	</div>
</div>
