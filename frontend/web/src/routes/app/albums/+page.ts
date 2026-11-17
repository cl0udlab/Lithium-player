import type { PageLoad } from './$types'
import { APIUrl } from '$lib/api'

export const load: PageLoad = async ({ fetch, url }) => {
	const parsed = Number(url.searchParams.get('page') || 1)
	const page = Number.isSafeInteger(parsed) && parsed > 0 ? parsed : 1
	const q = url.searchParams.get('q') || ''
	const cached = url.searchParams.get('cached') === 'true'
	const params = new URLSearchParams({ page: String(page), size: '24', q, cached: String(cached) })
	try {
		const response = await fetch(`${APIUrl}/library/albums?${params}`)
		if (!response.ok) throw new Error(`載入失敗 (${response.status})`)
		const result = await response.json()
		return {
			albums: result.items,
			total: result.total,
			page,
			size: 24,
			q,
			cached,
			error: null,
			status: 200
		}
	} catch (error) {
		return {
			albums: [],
			total: 0,
			page,
			size: 24,
			q,
			cached,
			error: error instanceof Error ? error.message : '無法連接到伺服器',
			status: 500
		}
	}
}
