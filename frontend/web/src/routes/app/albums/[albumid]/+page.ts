import type { PageLoad } from './$types'
import { APIUrl } from '$lib/api'

export const load: PageLoad = async ({ fetch, params }) => {
	const response = await fetch(`${APIUrl}/file/album?album_id=${params.albumid}`)
	const album = await response.json()
	return { album }
}
