<script lang="ts">
	import { goto } from '$app/navigation'
	import { onMount } from 'svelte'
	import type { PageData } from './$types'
	import 'vidstack/bundle'
	import type { MediaPlayerElement } from 'vidstack/elements'
  import { APIUrl } from '$lib/api'

	export let data: PageData
	const { video } = data
	let player: MediaPlayerElement

	function handleFullscreenChange() {
		if (!document.fullscreenElement) {
			handleClose()
		}
	}

	onMount(() => {
		const handleLoaded = () => {
			player?.enterFullscreen()
		}

		player?.addEventListener('can-play', handleLoaded)
		document.addEventListener('fullscreenchange', handleFullscreenChange)

		return () => {
			player?.exitFullscreen()
			player?.removeEventListener('can-play', handleLoaded)
			document.removeEventListener('fullscreenchange', handleFullscreenChange)
		}
	})

	function handleClose() {
		history.back()
	}
</script>

<svelte:head>
	<title>{video.title} - Lithium Player</title>
</svelte:head>

<div class="fixed inset-0 bg-black">
	<media-player bind:this={player} class="h-full" autoplay>
		<media-provider>
			<source src={`${APIUrl}/stream/video/${video.id}`} type="video/mp4" />
		</media-provider>
		<media-video-layout>
			<media-controls></media-controls>
		</media-video-layout>
	</media-player>
</div>
