import type { HandleFetch } from '@sveltejs/kit'
import { env } from '$env/dynamic/private'

// Universal page loads also run on a full-page reload. Route those API
// requests to the backend instead of SvelteKit's nonexistent /api routes.
export const handleFetch: HandleFetch = async ({ request, fetch, event }) => {
	const url = new URL(request.url)
	if (url.origin === event.url.origin && url.pathname.startsWith('/api/')) {
		const upstream = new URL(url.pathname.slice(4) + url.search, env.API_INTERNAL_URL || 'http://127.0.0.1:8000')
		return fetch(new Request(upstream, request))
	}
	return fetch(request)
}
