import type { PageLoad } from './$types'
import { APIUrl } from '$lib/api'

export const load: PageLoad = async ({ fetch, params }) => {
	const response = await fetch(`${APIUrl}/library/albums/${params.albumid}`)
	const album = await response.json()
	return { album }
}
