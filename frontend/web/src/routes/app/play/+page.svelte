<script lang="ts">
	import { playerState } from '$lib/stores/player';
	import { goto } from '$app/navigation';


	$effect(() => {
		if (!$playerState.currentTrack) {
			goto('/app');
		}
	});
</script>
