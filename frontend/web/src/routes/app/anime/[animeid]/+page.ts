import { error } from '@sveltejs/kit'
import { APIUrl } from '$lib/api'
import type { PageLoad } from './$types'

export const load = (async ({ fetch, params }) => {
	const response = await fetch(`${APIUrl}/video/anime/${params.animeid}`)
	if (!response.ok) error(response.status, '找不到這部動畫')
	const animes = await response.json()
	return {
		animes
	}
}) satisfies PageLoad
