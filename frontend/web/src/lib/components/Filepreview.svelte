<script lang="ts">
	import { onMount } from 'svelte'

	export let filePath: string
	export let fileType: string
	export let fileId: number
	export let onClose: () => void

	let content: string = ''
	let loading: boolean = true
	let error: string = ''

	async function loadFile() {
		try {
			const response = await fetch(`http://localhost:8000/stream/file/${fileId}`)
			if (!response.ok) throw new Error('檔案載入失敗')

			if (fileType === 'txt') {
				content = await response.text()
			} else {
				content = URL.createObjectURL(await response.blob())
			}
		} catch (e) {
			error = (e as Error).message
		} finally {
			loading = false
		}
	}

	onMount(() => {
		loadFile()
		return () => {
			if (content && fileType !== 'txt') {
				URL.revokeObjectURL(content)
			}
		}
	})
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
	<div class="h-4/5 w-4/5 overflow-hidden rounded-lg bg-white shadow-xl dark:bg-gray-800">
		<div class="flex h-full flex-col p-4">
			{#if loading}
				<div class="flex flex-1 items-center justify-center">
					<div class="loading-spinner text-primary">載入中...</div>
				</div>
			{:else if error}
				<div class="flex flex-1 items-center justify-center text-error">
					<p>{error}</p>
				</div>
			{:else}
				<div class="flex-1 overflow-auto">
					{#if fileType === 'pdf'}
						<iframe src={content} title="PDF檢視器" class="h-full w-full border-none"></iframe>
					{:else if fileType === 'epub' || fileType === 'mobi'}
						<pre class="whitespace-pre-wrap p-4">Not Yet</pre>
					{:else}
						<pre class="whitespace-pre-wrap p-4">{content}</pre>
					{/if}
				</div>
			{/if}

			<div class="mt-4 flex justify-end">
				<button class="btn btn-primary" on:click={onClose}>關閉</button>
			</div>
		</div>
	</div>
</div>
