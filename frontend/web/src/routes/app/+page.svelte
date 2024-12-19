<script lang="ts">
	import { stars } from '$lib/init/playerlist';
	import { onMount } from 'svelte';
	import { getContext } from 'svelte';
	import type { MusicTrack } from '$lib/types';

	onMount(() => {
		stars.initialize();
	});

	const playMusic = getContext<(track: MusicTrack) => void>('playMusic');

	function handlePlay(track: MusicTrack) {
		console.log(playMusic);
		playMusic(track);
	}
</script>

<button
	type="button"
	onclick={() =>
		handlePlay({ id: 2, title: 'test', artist: 'unknown', album: 'unknown',albumArt:"",})}
	aria-label="Play test track"
>
	<p>test click</p>
</button>
