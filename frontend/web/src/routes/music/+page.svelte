<script lang="ts">
	import { onMount } from 'svelte';
	import 'vidstack/bundle';
	import 'vidstack/player';
	import 'vidstack/player/layouts/default';
	import 'vidstack/player/ui';
</script>

<div class="mx-auto w-full max-w-3xl p-4">
	<media-player
		class="aspect-[16/9] w-full"
		viewType="audio"
		streamType="on-demand"
		logLevel="warn"
		crossOrigin
		playsInline
		title="Sprite Fight"
	>
		<media-provider>
			<source src="http://localhost:8000/api/stream/music/2" type="audio/flac" />
		</media-provider>

		<media-audio-layout>
			<media-controls>
				<media-control-bar>
					<media-play-button></media-play-button>
					<media-mute-button></media-mute-button>
					<media-volume-slider></media-volume-slider>
					<media-time-slider></media-time-slider>
					<media-time></media-time>
				</media-control-bar>
			</media-controls>
		</media-audio-layout>
	</media-player>
</div>

<style>
	:global(media-player) {
		--media-brand: theme(colors.indigo.600);
		--media-focus-ring: theme(colors.indigo.400);
		--media-controls-height: 45px;
	}
</style>
