<script lang="ts">
	import { goto } from '$app/navigation'
	import { onMount } from 'svelte'
	onMount(() => {
		void goto('/app/setting#subsonic', { replaceState: true })
	})
</script>

<p class="text-fg-muted">
	Subsonic 設定已移至<a class="text-accent" href="/app/setting#subsonic">設定</a>，音樂請至<a
		class="text-accent"
		href="/app/music">歌曲</a
	>與<a class="text-accent" href="/app/albums">專輯</a>瀏覽。
</p>
