<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { LayoutData } from './$types';
	import Navbar from '$lib/components/navbar.svelte';
	import Sidebar from '$lib/components/sidebar.svelte';
	import { onMount } from 'svelte';
	import 'vidstack/bundle';
	import 'vidstack/player';
	import 'vidstack/player/layouts/default';
	import 'vidstack/player/ui';
	import type { MediaPlayerElement } from 'vidstack/elements';

	let isExpanded = $state(true);
	let player: MediaPlayerElement;
	let playerisable = false;

	let { data, children }: { data: LayoutData; children: Snippet } = $props();
	function handleToggle(expanded: boolean) {
		isExpanded = expanded;
	}
</script>

<div class="flex min-h-screen flex-col">
	<header class="fixed top-0 z-50 w-full">
		<Navbar onToggle={handleToggle} />
	</header>

	<div class="flex flex-1 pb-24 pt-16">
		<Sidebar {isExpanded} />

		<main class={`flex-1 p-4 transition-all ${isExpanded ? 'pl-64' : 'pl-16'}`}>
			{@render children()}
		</main>

		{#if playerisable}
			<div
				class={`bg-base-100 t fixed bottom-0 left-0 right-0 z-50 transition-all ${isExpanded ? 'pl-64' : 'pl-16'}`}
			>
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
			</div>
		{/if}
	</div>
</div>
