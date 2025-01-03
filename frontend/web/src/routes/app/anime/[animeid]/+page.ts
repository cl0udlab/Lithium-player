import { APIUrl } from '$lib/api'
import type { PageLoad } from './$types'

export const load = (async ({ fetch, params }) => {
	const response = await fetch(`${APIUrl}/video/anime/${params.animeid}`)
	const animes = await response.json()
	return {
		animes
	}
}) satisfies PageLoad
