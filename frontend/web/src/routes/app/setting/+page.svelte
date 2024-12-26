<script lang="ts">
	import { on } from 'svelte/events';
	import type { PageData } from './$types';
	import { Folder, File } from 'lucide-svelte';
	let { data }: { data: PageData } = $props();

	interface DirectoryContent {
		files: string[];
		dirs: string[];
		path: string;
		error: string | null;
	}

	let isModalOpen = $state(false);
	let currentPath = $state('/');
	let files = $state<string[]>([]);
	let dirs = $state<string[]>([]);
	let error = $state<string | null>(null);
	let activeTab = $state('directory');
	let scanStatus = $state<string | null>(null);

	function handlePathInput() {
		if (currentPath) {
			fetchDirs(currentPath);
		}
	}
	async function fetchDirs(path: string) {
		try {
			const response = await fetch(
				`http://localhost:8000/setting/dir?path=${encodeURIComponent(path)}`
			);
			const data: DirectoryContent = await response.json();

			if (data.error) {
				error = data.error;
				return;
			}

			files = data.files;
			dirs = data.dirs;
			currentPath = data.path;
			error = null;
		} catch (err) {
			error = '取得目錄失敗';
		}
	}

	function handleDirClick(dir: string) {
		const newPath = currentPath === '/' ? `/${dir}` : `${currentPath}/${dir}`;
		fetchDirs(newPath);
	}
	function handleFileClick(file: string) {
		const newPath = currentPath === '/' ? `/${file}` : `${currentPath}/${file}`;
		currentPath = newPath;
	}

	function openModal() {
		isModalOpen = true;
		fetchDirs('/');
	}

	function closeModal() {
		isModalOpen = false;
		currentPath = '/';
		dirs = [];
		error = null;
	}

	function handleSelect() {
		console.log('selected path:', currentPath);
		closeModal();
	}
	async function handleScan() {
		try {
			scanStatus = '掃描中...';
			const response = await fetch(`http://localhost:8000/file/parse_file`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ file_path: currentPath })
			});

			const data = await response.json();
			if (response.status === 400) {
				error = data.detail;
				scanStatus = data.detail;
				setTimeout(() => {
					scanStatus = null;
				}, 3000);
				return;
			}

			console.log('掃描結果:', data);
			scanStatus = '掃描完成';
			setTimeout(() => {
				scanStatus = null;
			}, 3000);
		} catch (err) {
			error = '掃描失敗';
			scanStatus = null;
		}
	}

	async function handleScanDir() {
		try {
			scanStatus = '掃描中...';
			const response = await fetch(`http://localhost:8000/file/scanall`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ file_path: currentPath })
			});

			const data = await response.json();
			if (response.status === 400) {
				error = data.detail;
				scanStatus = data.detail;
				setTimeout(() => {
					scanStatus = null;
				}, 3000);
				return;
			}

			console.log('掃描結果:', data);
			scanStatus = '掃描完成';
			setTimeout(() => {
				scanStatus = null;
			}, 3000);
		} catch (err) {
			error = '掃描失敗';
			scanStatus = null;
		}
	}

	function handleTabChange(tab: string) {
		activeTab = tab;
	}
</script>

<div class="p-4">
	<h1 class="mb-6 text-2xl font-bold">系統設定</h1>

	<div class="card bg-base-200 shadow-xl">
		<div class="card-body">
			<h2 class="card-title">音樂掃描</h2>
			<p>選擇要掃描的音樂目錄</p>
			<div class="card-actions justify-end">
				<button class="btn btn-primary" onclick={openModal}>
					<Folder size={20} />
					選擇目錄
				</button>
			</div>
		</div>
	</div>
</div>

<dialog class="modal" class:modal-open={isModalOpen}>
	<div class="modal-box">
		<h3 class="mb-4 text-lg font-bold">掃描目錄</h3>
		<div class="tabs tabs-boxed mb-4">
			<button
				class="tab"
				class:tab-active={activeTab === 'directory'}
				onclick={() => handleTabChange('directory')}
			>
				掃描目錄
			</button>
			<button
				class="tab"
				class:tab-active={activeTab === 'scan'}
				onclick={() => handleTabChange('scan')}
			>
				掃描檔案
			</button>
		</div>
		{#if error}
			<div class="alert alert-error mb-4">
				<span>{error}</span>
			</div>
		{/if}
		{#if activeTab === 'directory'}
			<!-- 原有的目錄選擇介面 -->
			<div class="form-control mb-4">
				<div class="input-group flex flex-row">
					<input
						type="text"
						placeholder="輸入目錄路徑..."
						class="input input-bordered w-full"
						bind:value={currentPath}
						onkeypress={(e) => e.key === 'Enter' && handlePathInput()}
					/>
					<button class="btn btn-square" onclick={handlePathInput}> 前往 </button>
				</div>
			</div>
			<div class="breadcrumbs mb-4 text-sm">
				<ul>
					<li>
						<a
							href="#"
							onclick={(e) => {
								e.preventDefault();
								fetchDirs('/');
							}}
						>
							根目錄
						</a>
					</li>
					{#if currentPath !== '/'}
						{#each currentPath.split('/').filter(Boolean) as part, index}
							<li>
								<a
									href="#"
									onclick={(e) => {
										e.preventDefault();
										const path =
											'/' +
											currentPath
												.split('/')
												.filter(Boolean)
												.slice(0, index + 1)
												.join('/');
										fetchDirs(path);
									}}
								>
									{part}
								</a>
							</li>
						{/each}
					{/if}
				</ul>
			</div>
			<div class="max-h-96 overflow-y-auto">
				<table class="table-zebra table">
					<tbody> </tbody><tbody>
						{#each dirs as dir}
							<tr class="hover cursor-pointer" onclick={() => handleDirClick(dir)}>
								<td>
									<Folder size={20} class="text-primary mr-2 inline" />
									{dir}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<div class="modal-action">
				<button class="btn btn-ghost" onclick={closeModal}>取消</button>
				<button class="btn btn-primary" onclick={handleSelect}>開始掃描</button>
			</div>
		{:else}
			<div class="form-control">
				<div class="form-control mb-4">
					<div class="input-group flex flex-row">
						<input
							type="text"
							placeholder="輸入目錄路徑..."
							class="input input-bordered w-full"
							bind:value={currentPath}
							onkeypress={(e) => e.key === 'Enter' && handlePathInput()}
						/>
						<button class="btn btn-square" onclick={handlePathInput}> 前往 </button>
					</div>
				</div>
				<div class="breadcrumbs mb-4 text-sm">
					<ul>
						<li>
							<a
								href="#"
								onclick={(e) => {
									e.preventDefault();
									fetchDirs('/');
								}}
							>
								根目錄
							</a>
						</li>
						{#if currentPath !== '/'}
							{#each currentPath.split('/').filter(Boolean) as part, index}
								<li>
									<a
										href="#"
										onclick={(e) => {
											e.preventDefault();
											const path =
												'/' +
												currentPath
													.split('/')
													.filter(Boolean)
													.slice(0, index + 1)
													.join('/');
											fetchDirs(path);
										}}
									>
										{part}
									</a>
								</li>
							{/each}
						{/if}
					</ul>
				</div>
				{#if scanStatus}
					<div class="alert alert-info mb-4">
						<span>{scanStatus}</span>
					</div>
				{/if}
				<div class="max-h-96 overflow-y-auto">
					<table class="table-zebra table">
						<tbody>
							{#each dirs as dir}
								<tr class="hover cursor-pointer" onclick={() => handleDirClick(dir)}>
									<td>
										<Folder size={20} class="text-primary mr-2 inline" />
										{dir}
									</td>
								</tr>
							{/each}
							{#each files as file}
								<tr class="hover" onclick={() => handleFileClick(file)}>
									<td>
										<File size={20} class="text-secondary mr-2 inline" />
										{file}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
			<div class="modal-action">
				<button class="btn btn-ghost" onclick={closeModal}>取消</button>
				<button class="btn btn-primary" onclick={handleScanDir} disabled={scanStatus === '掃描中...'}>
					{scanStatus === '掃描中...' ? '掃描中...' : '開始掃描'}
				</button>
			</div>
		{/if}
	</div>
	<form method="dialog" class="modal-backdrop">
		<button onclick={closeModal}>關閉</button>
	</form>
</dialog>
