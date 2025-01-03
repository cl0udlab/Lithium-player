import type { PageLoad } from './$types'
import { APIUrl } from '$lib/api'
import Cookies from 'js-cookie'

export const load = (async ({ fetch, params }) => {
	try {
		const token = Cookies.get('access_token')

		const responsemusic = await fetch(`${APIUrl}/playlist/playlist/${params.playlistid}`, {
			headers: {
				Authorization: `Bearer ${token}`
			}
		})

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
