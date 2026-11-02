<script lang="ts">
	import { LoaderCircle } from 'lucide-svelte'

	let { class: className = 'h-5 w-5' }: { class?: string } = $props()
</script>

<LoaderCircle class="animate-spin {className}" aria-label="載入中" />
