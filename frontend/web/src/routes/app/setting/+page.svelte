<script lang="ts">
	import { Folder, File, FolderSearch, ChevronRight, HardDrive, ScanLine, FileSearch } from 'lucide-svelte'
	import { APIUrl } from '$lib/api'
	import { toast } from '$lib/stores/toast.svelte'
	import Button from '$lib/components/ui/Button.svelte'
	import Dialog from '$lib/components/ui/Dialog.svelte'
	import Input from '$lib/components/ui/Input.svelte'
	import PageHeader from '$lib/components/ui/PageHeader.svelte'
	import Spinner from '$lib/components/ui/Spinner.svelte'
	import Tabs from '$lib/components/ui/Tabs.svelte'

	interface DirectoryContent {
		files: string[]
		dirs: string[]
		path: string
		error: string | null
	}

	let dialogOpen = $state(false)
	let mode = $state<'directory' | 'file'>('directory')
	let currentPath = $state('/')
	let pathInput = $state('/')
	let files = $state<string[]>([])
	let dirs = $state<string[]>([])
	let browsing = $state(false)
	let scanning = $state(false)

	const crumbs = $derived(currentPath.split('/').filter(Boolean))

	async function fetchDirs(path: string) {
		browsing = true
		try {
			const response = await fetch(`${APIUrl}/setting/dir?path=${encodeURIComponent(path)}`)
			const result: DirectoryContent = await response.json()
			if (result.error) {
				toast.error('無法開啟目錄', result.error)
				return
			}
			files = result.files
			dirs = result.dirs
			currentPath = pathInput = result.path
		} catch {
			toast.error('取得目錄失敗')
		} finally {
			browsing = false
		}
	}

	const join = (name: string) => (currentPath === '/' ? `/${name}` : `${currentPath}/${name}`)

	function openDialog() {
		dialogOpen = true
		fetchDirs(currentPath)
	}

	async function scan() {
		scanning = true
		const endpoint = mode === 'directory' ? 'scanall' : 'parse_file'
		try {
			const response = await fetch(`${APIUrl}/file/${endpoint}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ file_path: pathInput })
			})
			const result = await response.json().catch(() => null)
			if (mode === 'directory' && response.status === 409) {
				toast.info('已經有掃描在進行中')
				dialogOpen = false
				pollScanStatus()
				return
			}
			if (!response.ok) {
				toast.error('掃描失敗', result?.detail ?? `HTTP ${response.status}`)
				return
			}
			dialogOpen = false
			if (mode === 'directory') {
				scanStatus = result
				toast.info('開始掃描', '在背景進行, 可以繼續使用')
				pollScanStatus()
			} else {
				toast.success('掃描完成', pathInput)
			}
		} catch {
			toast.error('掃描失敗', '無法連接到伺服器')
		} finally {
			scanning = false
		}
	}

	interface ScanStatus {
		running: boolean
		processed: number
		total: number
		current_file: string | null
		added: number
		removed: number
		error: string | null
	}

	let scanStatus = $state<ScanStatus | null>(null)
	let pollTimer: ReturnType<typeof setTimeout> | undefined

	async function pollScanStatus() {
		clearTimeout(pollTimer)
		try {
			const response = await fetch(`${APIUrl}/file/scanall/status`)
			if (!response.ok) throw new Error(`HTTP ${response.status}`)
			const wasRunning = scanStatus?.running
			scanStatus = await response.json()
			if (scanStatus?.running) {
				pollTimer = setTimeout(pollScanStatus, 1500)
			} else if (wasRunning && scanStatus) {
				if (scanStatus.error) toast.error('掃描失敗', scanStatus.error)
				else {
					const removed = scanStatus.removed ? `, 移除 ${scanStatus.removed} 首已不存在的音樂` : ''
					toast.success('掃描完成', `新增 ${scanStatus.added} 個檔案${removed}`)
				}
			}
		} catch {
			pollTimer = setTimeout(pollScanStatus, 5000)
		}
	}

	$effect(() => {
		// 重新整理頁面時接續顯示還在跑的掃描
		pollScanStatus()
		return () => clearTimeout(pollTimer)
	})

	const scanRunning = $derived(scanStatus?.running ?? false)
	const scanPercent = $derived(
		scanStatus?.total ? Math.round((scanStatus.processed / scanStatus.total) * 100) : 0
	)
</script>

<svelte:head>
	<title>設定 - Lithium Player</title>
</svelte:head>

<PageHeader title="設定" />

<div class="flex max-w-3xl flex-col gap-4">
	<section class="rounded-2xl border border-line/5 bg-surface p-6">
		<div class="flex items-start gap-4">
			<div class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-accent/10 text-accent">
				<HardDrive class="h-5 w-5" />
			</div>
			<div class="min-w-0 flex-1">
				<h2 class="font-semibold">媒體庫</h2>
				<p class="mt-1 text-sm text-fg-muted">
					掃描伺服器上的資料夾, 加入音樂、影片和文件。已經在媒體庫的檔案會自動略過, 檔案已經不見的音樂會從媒體庫移除。
				</p>
				{#if scanRunning && scanStatus}
					<div class="mt-4">
						<div class="flex items-center justify-between gap-2 text-xs text-fg-muted">
							<span class="flex items-center gap-2">
								<Spinner class="h-3 w-3" /> 背景掃描中
							</span>
							<span class="font-mono">
								{scanStatus.total ? `${scanStatus.processed} / ${scanStatus.total}` : '列出檔案中…'}
							</span>
						</div>
						<div class="mt-2 h-1.5 overflow-hidden rounded-full bg-line/10">
							<div class="h-full bg-accent transition-[width]" style="width: {scanPercent}%"></div>
						</div>
						{#if scanStatus.current_file}
							<p class="mt-1 truncate font-mono text-xs text-fg-subtle">{scanStatus.current_file}</p>
						{/if}
					</div>
				{/if}
			</div>
			<Button variant="primary" onclick={openDialog} disabled={scanRunning}>
				<FolderSearch class="h-4 w-4" /> 掃描
			</Button>
		</div>
	</section>

	<section class="rounded-2xl border border-line/5 bg-surface p-6">
		<h2 class="font-semibold">播放器</h2>
		<p class="mt-1 text-sm text-fg-muted">
			顯示模式、背景圖片 / 影片和亮度, 都在全螢幕播放器右下角的設定按鈕調整。
		</p>
	</section>
</div>

<Dialog
	bind:open={dialogOpen}
	title="掃描"
	description="選擇要掃描的資料夾或單一檔案"
	class="w-[min(40rem,calc(100vw-2rem))]"
>
	<Tabs
		bind:value={mode}
		items={[
			{ value: 'directory', label: '整個資料夾', icon: ScanLine },
			{ value: 'file', label: '單一檔案', icon: FileSearch }
		]}
	>
		{#snippet content(current)}
			<form
				class="flex gap-2"
				onsubmit={(e) => {
					e.preventDefault()
					fetchDirs(pathInput)
				}}
			>
				<Input bind:value={pathInput} placeholder="/music" class="flex-1 font-mono" />
				<Button type="submit">前往</Button>
			</form>

			<nav class="mt-3 flex flex-wrap items-center gap-0.5 text-sm text-fg-muted">
				<button class="rounded px-1.5 py-0.5 hover:bg-line/5 hover:text-fg" onclick={() => fetchDirs('/')}>
					根目錄
				</button>
				{#each crumbs as part, i}
					<ChevronRight class="h-3.5 w-3.5 text-fg-subtle" />
					<button
						class="rounded px-1.5 py-0.5 hover:bg-line/5 hover:text-fg"
						onclick={() => fetchDirs('/' + crumbs.slice(0, i + 1).join('/'))}
					>
						{part}
					</button>
				{/each}
			</nav>

			<div class="mt-3 h-72 overflow-y-auto rounded-xl border border-line/5 bg-bg/40 p-1">
				{#if browsing}
					<div class="grid h-full place-items-center"><Spinner /></div>
				{:else}
					{#each dirs as dir (dir)}
						<button
							class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm hover:bg-line/5"
							onclick={() => fetchDirs(join(dir))}
						>
							<Folder class="h-4 w-4 shrink-0 text-accent" />
							<span class="truncate">{dir}</span>
						</button>
					{/each}
					{#if current === 'file'}
						{#each files as file (file)}
							<button
								class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm hover:bg-line/5 {pathInput ===
								join(file)
									? 'bg-accent/10 text-accent'
									: ''}"
								onclick={() => (pathInput = join(file))}
							>
								<File class="h-4 w-4 shrink-0 text-fg-subtle" />
								<span class="truncate">{file}</span>
							</button>
						{/each}
					{/if}
					{#if dirs.length === 0 && (current === 'directory' || files.length === 0)}
						<p class="py-10 text-center text-sm text-fg-subtle">這個資料夾是空的</p>
					{/if}
				{/if}
			</div>
		{/snippet}
	</Tabs>
	{#snippet footer()}
		<p class="mr-auto self-center truncate font-mono text-xs text-fg-subtle">{pathInput}</p>
		<Button variant="ghost" onclick={() => (dialogOpen = false)}>取消</Button>
		<Button variant="primary" onclick={scan} disabled={scanning}>
			{#if scanning}<Spinner class="h-4 w-4" /> 掃描中…{:else}開始掃描{/if}
		</Button>
	{/snippet}
</Dialog>
