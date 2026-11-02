import { apiFetch } from '$lib/api'

export interface BangumiCandidate {
	id: number
	name: string
	name_cn: string
	air_date: string
	image: string | null
}

export interface RefreshOptions {
	bangumi_id?: number
	search_title?: string
}

type Result<T> = { ok: true; data: T } | { ok: false; detail: string }

async function send<T>(path: string, init: RequestInit): Promise<Result<T>> {
	const response = await apiFetch(path, init)
	const body = response.status === 204 ? null : await response.json().catch(() => null)
	if (!response.ok) return { ok: false, detail: body?.detail ?? `HTTP ${response.status}` }
	return { ok: true, data: body as T }
}

function post<T>(path: string, options: RefreshOptions) {
	return send<T>(path, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(options)
	})
}

export const deleteVideo = (id: number) => send<null>(`/video/${id}`, { method: 'DELETE' })

export const deleteAnime = (id: number) => send<null>(`/video/anime/${id}`, { method: 'DELETE' })

export const refreshVideo = (id: number, options: RefreshOptions = {}) =>
	post<{ id: number; series_id: number | null }>(`/video/${id}/refresh`, options)

export const refreshAnime = (id: number, options: RefreshOptions = {}) =>
	post<{ id: number | null }>(`/video/anime/${id}/refresh`, options)

export async function searchBangumi(query: string): Promise<BangumiCandidate[]> {
	const result = await send<BangumiCandidate[]>(
		`/video/bangumi/search?q=${encodeURIComponent(query)}`,
		{}
	)
	return result.ok ? result.data : []
}
