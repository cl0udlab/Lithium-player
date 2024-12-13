<script lang="ts">
	import { onMount } from 'svelte';
	import 'vidstack/bundle';
	import 'vidstack/player';
	import 'vidstack/player/layouts/default';
	import 'vidstack/player/ui';
	import type { MediaPlayerElement } from 'vidstack/elements';

	let player: MediaPlayerElement;
</script>

<div class="mx-auto w-full max-w-3xl p-4">
	<media-player
		class="aspect-[16/9] w-full"
		viewType="audio"
		streamType="on-demand"
		logLevel="debug"
		crossOrigin
		playsInline
		title="Sprite Fight"
		src='http://localhost:8000/stream/music/2'
		bind:this={player}
	>
		<media-provider></media-provider>
		<media-audio-layout></media-audio-layout>
	</media-player>
</div>
