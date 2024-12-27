import type { PageLoad } from './$types'
import { APIUrl } from '$lib/api'

export const load = (async ({ fetch }) => {
	try {
		const response = await fetch(`${APIUrl}/file/video`)

		if (!response.ok) {
			return {
				videos: [],
				error: `載入失敗: ${response.statusText}`,
				status: response.status
			}
		}

		const videos = await response.json()
		return {
			videos,
			error: null,
			status: 200
		}
	} catch (e) {
		console.error(e)
		return {
			videos: [],
			error: '無法連接到伺服器',
			status: 500
		}
	}
}) satisfies PageLoad
