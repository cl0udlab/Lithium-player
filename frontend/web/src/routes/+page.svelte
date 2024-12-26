<script lang="ts">
	import { onMount } from 'svelte'
	import { goto } from '$app/navigation'
	import Cookies from 'js-cookie'

	onMount(() => {
		if (Cookies.get('access_token')) {
			goto('/app')
		} else {
			goto('/login')
		}
	})
</script>
