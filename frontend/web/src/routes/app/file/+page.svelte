<script lang="ts">
	import { FileText, FileImage, FileMusic, FileVideo, File, BookOpen } from 'lucide-svelte'
	import type { Filei } from '$lib/types'
	import FilePreview from '$lib/components/Filepreview.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import type { PageData } from './$types'

	let { data }: { data: PageData } = $props()

	const files: any[] = $derived(data.files ?? [])
	let selected = $state<Filei | null>(null)

	const icons: Record<string, typeof File> = {
		image: FileImage,
		audio: FileMusic,
		video: FileVideo,
		text: FileText,
		txt: FileText,
		pdf: BookOpen,
		epub: BookOpen,
		mobi: BookOpen
	}

	function formatFileSize(bytes: number) {
		if (!bytes) return '0 B'
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
		const i = Math.floor(Math.log(bytes) / Math.log(1024))
		return `${(bytes / Math.pow(1024, i)).toFixed(i ? 1 : 0)} ${sizes[i]}`
	}
</script>

<svelte:head>
	<title>檔案 - Lithium Player</title>
</svelte:head>

<FilePreview bind:file={selected} />

{#if data.error}
	<StatusMessage kind="error" title="載入失敗" message={data.error} retry={data.status === 500} />
{:else}
	<PageHeader title="檔案" subtitle="{files.length} 個文件" />
	{#if files.length}
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
			{#each files as file (file.id)}
				{@const Icon = icons[file.file_format?.toLowerCase()] ?? File}
				<button
					class="flex items-center gap-4 rounded-xl border border-line/5 bg-surface p-4 text-left transition-colors hover:border-line/15 hover:bg-surface-2"
					onclick={() => (selected = file)}
				>
					<div class="grid h-12 w-12 shrink-0 place-items-center rounded-lg bg-accent/10 text-accent">
						<Icon class="h-6 w-6" />
					</div>
					<div class="min-w-0">
						<p class="truncate text-sm font-semibold">{file.name}</p>
						<p class="truncate text-xs text-fg-muted">
							{file.file_format?.toUpperCase()} · {formatFileSize(file.size)}
							{#if file.pages}· {file.pages} 頁{/if}
						</p>
						{#if file.author || file.publisher}
							<p class="mt-0.5 truncate text-xs text-fg-subtle">
								{[file.author, file.publisher].filter(Boolean).join(' · ')}
							</p>
						{/if}
					</div>
				</button>
			{/each}
		</div>
	{:else}
		<StatusMessage icon={FileText} title="還沒有文件" message="掃描時遇到的 PDF / TXT / EPUB 會出現在這裡。" />
	{/if}
{/if}
