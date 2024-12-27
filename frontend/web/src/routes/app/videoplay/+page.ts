import type { PageLoad } from './$types'
import { error } from '@sveltejs/kit'
import { APIUrl } from '$lib/api'

export const load: PageLoad = async ({ url, fetch }) => {
	const videoId = url.searchParams.get('id')

	if (!videoId) {
		throw error(400, '未提供影片 ID')
	}

	try {
		const response = await fetch(`${APIUrl}/file/video?video_id=${videoId}`)
		if (!response.ok) throw new Error('影片載入失敗')

		const video = await response.json()
		return { video }
	} catch (e) {
		throw error(404, '找不到影片')
	}
}
