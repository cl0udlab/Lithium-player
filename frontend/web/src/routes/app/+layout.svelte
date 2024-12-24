<!-- routes/app/+layout.svelte -->
<script lang="ts">
	import { setContext, type Snippet } from 'svelte';
	import type { LayoutData } from './$types';
	import { ChevronUp } from 'lucide-svelte';
	import { playerState } from '$lib/stores/player';
	import { goto } from '$app/navigation';
	import Navbar from '$lib/components/navbar.svelte';
	import Sidebar from '$lib/components/sidebar.svelte';
	import 'vidstack/bundle';

	import type { MediaPlayerElement } from 'vidstack/elements';
	import { browser } from '$app/environment';
	import { writable } from 'svelte/store';
	import { setCookie } from '$lib/util';
	import { page } from '$app/stores';
	import type { MusicTrack, Video } from '$lib/types';

	let player = $state<MediaPlayerElement | null>(null);
	let playerisable = $state(false);
	let showMusicDetail = $state(false);

	let { data, children }: { data: LayoutData; children: Snippet } = $props();
	const isExpanded = writable<boolean>(data.isExpanded);
	const currentTrack = writable<MusicTrack | null>(null);
	const isPlaying = writable(false);

  function stopMusic() {
    if(player) {
      player.pause();
      player.src = '';
      $isPlaying = false;
      playerisable = false;
    }
  }

	function playMusic(track: MusicTrack) {
		$currentTrack = track;
		$playerState.currentTrack = track;
		playerisable = true;

		const explay = async () => {
			if (player) {
				player.src = `http://localhost:8000/stream/music/${track.id}`;
			}
			await new Promise((resolve, reject) => {
				const onCanPlay = () => {
					player?.removeEventListener('can-play', onCanPlay);
					resolve(true);
				};

				const onError = (error: any) => {
					player?.removeEventListener('error', onError);
					reject(error);
				};

				player?.addEventListener('can-play', onCanPlay);
				player?.addEventListener('error', onError);
			});
			await player?.play();
		};

		if ($isPlaying) {
			explay();
			return;
		}
		const initPlayer = async () => {
			while (!player) {
				await new Promise((resolve) => setTimeout(resolve, 100));
			}

			try {
				player.src = `http://localhost:8000/stream/music/${track.id}`;
				await new Promise((resolve, reject) => {
					const onCanPlay = () => {
						player?.removeEventListener('can-play', onCanPlay);
						resolve(true);
					};

					const onError = (error: any) => {
						player?.removeEventListener('error', onError);
						reject(error);
					};

					player?.addEventListener('can-play', onCanPlay);
					player?.addEventListener('error', onError);
				});

				await player.play();
				$isPlaying = true;
			} catch (error) {
				console.error('播放失敗:', error);
			}
		};

		initPlayer();
	}

	function playVideo(video: Video) {
    stopMusic();
		goto(`/app/videoplay?id=${video.id}`);
	}

	function toggleMusicDetail() {
		showMusicDetail = !showMusicDetail;
	}

	function toggleSidebar() {
		isExpanded.update((value) => {
			const newValue = !value;
			if (browser) {
				setCookie('isExpanded', String(newValue));
			}
			return newValue;
		});
	}

	function togglePlayer() {
		$playerState.isExpanded = !$playerState.isExpanded;
		if ($playerState.isExpanded) {
			goto('/app/play');
		} else {
			history.back();
		}
	}

	setContext('playMusic', playMusic);
	setContext('playVideo', playVideo);
  setContext('stopMusic', stopMusic);

	$effect(() => {
		if ($page.route.id === '/app/play') {
			$playerState.isExpanded = true;
		} else {
			$playerState.isExpanded = false;
		}
	});
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

		{#if playerisable}
			<div
				class={`bg-base-100 fixed left-0 right-0 flex w-full flex-col transition-all duration-300 ${$playerState.isExpanded ? 'bottom-0 top-20' : 'bottom-0 h-24'} ${$isExpanded ? 'pl-64' : 'pl-16'}`}
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
									<div class="flex items-center justify-center">
										<img
											src={$playerState.currentTrack?.albumArt ||
												'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQI2K58h03rEdQC6vbTQhY3USrZ_FT-peeH4g&s'}
											alt="Album art"
											class="w-full max-w-md rounded-lg shadow-lg"
										/>
									</div>
									<div class="flex flex-col">
										<h2 class="mb-2 text-2xl font-bold">{$playerState.currentTrack?.title}</h2>
										<p class="mb-8 text-lg opacity-75">{$playerState.currentTrack?.artist}</p>
										<media-audio-layout>
											<media-controls class="flex flex-col gap-4">
												<media-time-slider class="w-full"></media-time-slider>
												<div class="flex items-center justify-center gap-4">
													<media-play-button></media-play-button>
													<media-mute-button></media-mute-button>
													<media-volume-slider></media-volume-slider>
													<media-time-display></media-time-display>
												</div>
											</media-controls>
										</media-audio-layout>
										<button class="btn btn-ghost" onclick={togglePlayer}>
											<ChevronUp class="rotate-180" />
										</button>
									</div>
								</div>
							</div>
						{:else}
							<div class="grid h-24 w-full grid-cols-[auto_1fr_auto] items-center gap-4 px-4">
								<div class="flex items-center gap-4">
									<img
										src={$playerState.currentTrack?.albumArt ||
											'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQI2K58h03rEdQC6vbTQhY3USrZ_FT-peeH4g&s'}
										alt="Album art"
										class="h-16 w-16 rounded-lg object-cover"
									/>
									<div>
										<h3 class="text-lg font-medium">{$playerState.currentTrack?.title}</h3>
										<p class="text-sm opacity-75">{$playerState.currentTrack?.artist}</p>
									</div>
								</div>
								<media-audio-layout class="w-full flex-1"></media-audio-layout>
								<button class="btn btn-ghost" onclick={togglePlayer}>
									<ChevronUp />
								</button>
							</div>
						{/if}
					</media-player>
				</div>
			</div>
		{/if}
	</div>
</div>
