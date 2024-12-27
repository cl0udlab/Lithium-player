import type { PageLoad } from './$types'
import { APIUrl } from '$lib/api'

export const load = (async ({ fetch }) => {
	try {
		const response = await fetch(`${APIUrl}/file/file`)

		if (!response.ok) {
			return {
				files: [],
				error: `載入失敗: ${response.statusText}`,
				status: response.status
			}
		}

		const files = await response.json()
		console.log(files)
		return {
			files,
			error: null,
			status: 200
		}
	} catch (e) {
		console.error(e)
		return {
			files: [],
			error: '無法連接到伺服器',
			status: 500
		}
	}
}) satisfies PageLoad
