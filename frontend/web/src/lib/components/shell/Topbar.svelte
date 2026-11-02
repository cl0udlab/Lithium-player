<script lang="ts">
	import { ChevronLeft, ChevronRight } from 'lucide-svelte'
	import SearchBox from './SearchBox.svelte'
	import UserMenu from './UserMenu.svelte'
</script>

<header
	class="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-line/5 bg-bg px-6 md:px-8"
>
	<div class="hidden items-center gap-1 sm:flex">
		<button
			class="grid h-8 w-8 place-items-center rounded-full bg-surface-2 text-fg-muted hover:text-fg"
			onclick={() => history.back()}
			aria-label="上一頁"
		>
			<ChevronLeft class="h-4 w-4" />
		</button>
		<button
			class="grid h-8 w-8 place-items-center rounded-full bg-surface-2 text-fg-muted hover:text-fg"
			onclick={() => history.forward()}
			aria-label="下一頁"
		>
			<ChevronRight class="h-4 w-4" />
		</button>
	</div>
	<SearchBox />
	<div class="ml-auto">
		<UserMenu />
	</div>
</header>
