import Cookies from 'js-cookie'
import { browser } from '$app/environment'
import { goto } from '$app/navigation'

export const APIUrl = import.meta.env.DEV ? 'http://localhost:8000' : '/api'

export function coverUrl(coverArt: string | null | undefined, size = 300): string | null {
	if (!coverArt) return null
	if (/^https?:\/\//.test(coverArt)) return coverArt
	return `${APIUrl}/file/image?image_id=${coverArt}&image_size=${size}`
}

let refreshing: Promise<boolean> | null = null

async function refreshAccessToken(fetchFn: typeof fetch): Promise<boolean> {
	const refreshToken = Cookies.get('refresh_token')
	if (!refreshToken) return false
	try {
		const response = await fetchFn(
			`${APIUrl}/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`,
			{ method: 'POST' }
		)
		if (!response.ok) return false
		const data = await response.json()
		Cookies.set('access_token', data.access_token)
		if (data.refresh_token) Cookies.set('refresh_token', data.refresh_token)
		return true
	} catch {
		return false
	}
}

export async function apiFetch(
	path: string,
	init: RequestInit = {},
	fetchFn: typeof fetch = fetch
): Promise<Response> {
	const send = () => {
		const headers = new Headers(init.headers)
		const token = Cookies.get('access_token')
		if (token) headers.set('Authorization', `Bearer ${token}`)
		return fetchFn(`${APIUrl}${path}`, { ...init, headers })
	}

	const response = await send()
	if (response.status !== 401 || !browser) return response

	refreshing ??= refreshAccessToken(fetchFn).finally(() => (refreshing = null))
	if (await refreshing) return send()

	Cookies.remove('access_token')
	Cookies.remove('refresh_token')
	await goto('/login')
	return response
}
