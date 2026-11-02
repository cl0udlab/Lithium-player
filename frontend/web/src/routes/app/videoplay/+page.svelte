<script lang="ts">
	import { onMount } from 'svelte'
	import type { PageData } from './$types'
	import { Play, Pause, X } from 'lucide-svelte'
	import { APIUrl } from '$lib/api'

	let { data }: { data: PageData } = $props()
	const { video } = data
	let player: HTMLVideoElement
	let showControls = $state(true)
	let controlsTimeout: ReturnType<typeof setTimeout>
	let isPlaying = $state(false)

	function handleFullscreenChange() {
		if (!document.fullscreenElement) {
			handleClose()
		}
	}

	onMount(() => {
		const handleLoaded = () => {
			player?.requestFullscreen().catch(() => {})
		}

		player?.addEventListener('canplay', handleLoaded)
		player?.addEventListener('play', () => (isPlaying = true))
		player?.addEventListener('pause', () => (isPlaying = false))
		document.addEventListener('fullscreenchange', handleFullscreenChange)

		return () => {
			if (document.fullscreenElement) {
				document.exitFullscreen().catch(() => {})
			}
			player?.removeEventListener('canplay', handleLoaded)
			document.removeEventListener('fullscreenchange', handleFullscreenChange)
		}
	})

	function handleClose() {
		history.back()
	}

	function togglePlay() {
		if (!player) return
		if (player.paused) {
			player.play()
		} else {
			player.pause()
		}
	}

	function onMouseMove() {
		showControls = true
		clearTimeout(controlsTimeout)
		controlsTimeout = setTimeout(() => {
			showControls = false
		}, 3000)
	}
</script>

<svelte:head>
	<title>{video.title} - Lithium Player</title>
</svelte:head>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="fixed inset-0 bg-black"
	onmousemove={onMouseMove}
	role="region"
	aria-label="Video player"
>
	<video
		bind:this={player}
		class="h-full w-full"
		autoplay
		src={`${APIUrl}/stream/video/${video.id}`}
	>
		<track kind="captions" />
	</video>


	<div
		class={`absolute inset-0 flex flex-col justify-between bg-linear-to-t from-black/60 via-transparent to-black/30 p-4 transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}
	>

		<div class="flex items-center justify-between">
			<h1 class="text-lg font-semibold text-white drop-shadow-sm">{video.title}</h1>
			<button class="grid h-10 w-10 place-items-center rounded-full text-white hover:bg-white/15" onclick={handleClose}>
				<X size={20} />
			</button>
		</div>


		<div class="flex items-center justify-center">
			<button
				class="grid h-20 w-20 place-items-center rounded-full bg-black/30 text-white opacity-80 backdrop-blur-sm transition hover:scale-105 hover:opacity-100"
				onclick={togglePlay}
			>
				{#if isPlaying}
					<Pause size={36} />
				{:else}
					<Play size={36} />
				{/if}
			</button>
		</div>


		<div></div>
	</div>
</div>
