import type { PageLoad } from './$types'
import { APIUrl } from '$lib/api'

export const load = (async ({ fetch }) => {
	try {
		const response = await fetch(`${APIUrl}/file/album`)

		if (!response.ok) {
			return {
				albums: [],
				error: `載入失敗: ${response.statusText}`,
				status: response.status
			}
		}

		const albums = await response.json()
		console.log(albums)
		return {
			albums,
			error: null,
			status: 200
		}
	} catch (e) {
		console.error(e)
		return {
			albums: [],
			error: '無法連接到伺服器',
			status: 500
		}
	}
}) satisfies PageLoad
