<script lang="ts">
	import { APIUrl } from '$lib/api'
	import Dialog from '$lib/components/ui/Dialog.svelte'
	import Button from '$lib/components/ui/Button.svelte'
	import EbookReader from '$lib/components/EbookReader.svelte'
	import Spinner from '$lib/components/ui/Spinner.svelte'
	import StatusMessage from '$lib/components/ui/StatusMessage.svelte'
	import type { Filei } from '$lib/types'

	let { file = $bindable() }: { file: (Filei & { name?: string }) | null } = $props()

	let open = $state(false)
	let content = $state('')
	let book = $state<File | null>(null)
	let loading = $state(true)
	let error = $state('')

	const isEbook = (format?: string) => format === 'epub' || format === 'mobi'

	$effect(() => {
		if (!file) return
		const current = file
		open = true
		loading = true
		error = ''
		book = null
		let objectUrl = ''
		fetch(`${APIUrl}/stream/file/${current.id}`)
			.then(async (response) => {
				if (!response.ok) throw new Error('檔案載入失敗')
				if (current.file_format === 'txt') {
					content = await response.text()
				} else if (isEbook(current.file_format)) {
					const name = current.filepath.split(/[\\/]/).pop() ?? `book.${current.file_format}`
					book = new File([await response.blob()], name)
				} else {
					objectUrl = URL.createObjectURL(await response.blob())
					content = objectUrl
				}
			})
			.catch((e) => (error = (e as Error).message))
			.finally(() => (loading = false))
		return () => {
			if (objectUrl) URL.revokeObjectURL(objectUrl)
		}
	})

	$effect(() => {
		if (!open && file) file = null
	})
</script>

<Dialog bind:open title={file?.name ?? '檔案預覽'} class="h-[85vh] w-[min(64rem,calc(100vw-2rem))]">
	{#if loading}
		<div class="grid h-full place-items-center"><Spinner class="h-6 w-6" /></div>
	{:else if error}
		<StatusMessage kind="error" title="無法預覽" message={error} />
	{:else if file?.file_format === 'pdf'}
		<iframe
			src={content}
			title="PDF 檢視器"
			class="h-full min-h-[70vh] w-full rounded-lg border-none"
		></iframe>
	{:else if isEbook(file?.file_format) && book}
		{#key book}
			<EbookReader file={book} />
		{/key}
	{:else}
		<pre class="font-mono text-sm leading-relaxed whitespace-pre-wrap text-fg-muted">{content}</pre>
	{/if}
	{#snippet footer()}
		<Button onclick={() => (open = false)}>關閉</Button>
	{/snippet}
</Dialog>
