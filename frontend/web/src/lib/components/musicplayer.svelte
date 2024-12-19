<script lang="ts">
	import 'vidstack/bundle';
	import 'vidstack/player';
	import 'vidstack/player/layouts/default';
	import 'vidstack/player/ui';
	import type { MediaPlayerElement } from 'vidstack/elements';
	let player = $state<MediaPlayerElement | null>(null);
</script>

<media-player
	class="h-full w-full"
	viewType="audio"
	streamType="on-demand"
	logLevel="debug"
	crossOrigin
	playsInline
	title="Sprite Fight"
	src="http://localhost:8000/stream/music/2"
	bind:this={player}
>
	<media-provider></media-provider>
	<media-audio-layout></media-audio-layout>
</media-player>
