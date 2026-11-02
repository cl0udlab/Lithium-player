import type { PageLoad } from './$types'
import { apiFetch } from '$lib/api'

// token 存在 js-cookie, 只有瀏覽器讀得到, SSR 時會變成沒登入
export const ssr = false

export const load = (async ({ fetch }) => {
	try {
		const responsemusic = await apiFetch('/playlist/playlist', {}, fetch)

		if (!responsemusic.ok) {
			return {
				playlist: [],
				error: `載入失敗: ${responsemusic.statusText}`,
				status: responsemusic.status
			}
		}

		const playlist = await responsemusic.json()
		return {
			playlist,
			error: null,
			status: 200
		}
	} catch (e) {
		console.error(e)
		return {
			playlist: [],
			error: '無法連接到伺服器',
			status: 500
		}
	}
}) satisfies PageLoad
