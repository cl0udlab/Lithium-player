import type { PageLoad } from './$types'
import { APIUrl } from '$lib/api'

export const load = (async ({ fetch }) => {
	try {
		const responsemusic = await fetch(`${APIUrl}/file/info`)

		if (!responsemusic.ok) {
			return {
				info: [],
				error: `載入失敗: ${responsemusic.statusText}`,
				status: responsemusic.status
			}
		}

		const info = await responsemusic.json()
		console.log(info)
		return {
			info,
			error: null,
			status: 200
		}
	} catch (e) {
		console.error(e)
		return {
			info: [],
			error: '無法連接到伺服器',
			status: 500
		}
	}
}) satisfies PageLoad
