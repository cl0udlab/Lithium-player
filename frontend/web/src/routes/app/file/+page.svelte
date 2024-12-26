<script lang="ts">
	export let data
	import type { Filei } from '$lib/types'
	import { FileText, FileImage, FileMusic, FileVideo, File } from 'lucide-svelte'
	import FilePreview from '$lib/components/Filepreview.svelte'
	import { onMount } from 'svelte'

	const { files, error, status } = data

	function getFileIcon(format: string) {
		switch (format.toLowerCase()) {
			case 'image':
				return FileImage
			case 'audio':
				return FileMusic
			case 'video':
				return FileVideo
			case 'text':
				return FileText
			default:
				return File
		}
	}

	function formatFileSize(bytes: number) {
		const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
		if (bytes === 0) return '0 Byte'
		const i = Math.floor(Math.log(bytes) / Math.log(1024))
		return Math.round(bytes / Math.pow(1024, i)) + ' ' + sizes[i]
	}
	let showPreview = false
	let selectedFile: Filei | null = null

	function openPreview(file: Filei) {
		selectedFile = file
		showPreview = true
	}

	function handelEsc(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			showPreview = false
		}
	}

	onMount(() => {
		window.addEventListener('keydown', handelEsc)
		return () => {
			window.removeEventListener('keydown', handelEsc)
		}
	})
</script>

<svelte:head>
	<title>檔案 - Lithium Player</title>
</svelte:head>

{#if showPreview && selectedFile !== null}
	<FilePreview
		filePath={selectedFile.filepath}
		fileType={selectedFile.file_format}
		fileId={selectedFile.id}
		onClose={() => (showPreview = false)}
	/>
{/if}

{#if error}
	<div class="flex flex-col items-center justify-center p-8 text-error">
		<h2 class="mb-4 text-2xl font-bold">載入失敗</h2>
		<p class="text-lg">{error}</p>
		{#if status === 500}
			<button type="button" class="btn btn-error mt-4" onclick={() => window.location.reload()}>
				重試
			</button>
		{/if}
	</div>
{:else}
	<div class="grid grid-cols-1 gap-5 p-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
		{#each files as file}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				class="overflow-hidden rounded-lg bg-base-200 shadow-lg transition-shadow hover:shadow-xl"
				onclick={() => openPreview(file)}
			>
				<div
					class="overflow-hidden rounded-lg bg-base-200 shadow-lg transition-shadow hover:shadow-xl"
				>
					<div class="group relative flex items-center justify-center p-6">
						<svelte:component
							this={getFileIcon(file.file_format)}
							size={64}
							class="text-gray-600"
						/>
					</div>
					<div class="p-4">
						<h3 class="truncate text-lg font-semibold">{file.name}</h3>
						<p class="truncate text-sm text-gray-500">{formatFileSize(file.size)}</p>
						{#if file.author}
							<p class="truncate text-xs text-gray-400">作者: {file.author}</p>
						{/if}
						{#if file.publisher}
							<p class="truncate text-xs text-gray-400">出版商: {file.publisher}</p>
						{/if}
						{#if file.pages}
							<p class="truncate text-xs text-gray-400">頁數: {file.pages}</p>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}
