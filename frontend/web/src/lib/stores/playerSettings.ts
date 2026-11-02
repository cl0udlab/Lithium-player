import { writable } from 'svelte/store'
import { browser } from '$app/environment'
import { APIUrl } from '$lib/api'

export type DisplayMode = 'lyrics' | 'art'

export interface PlayerBackground {
	source: 'cover' | 'custom'
	url: string | null
	type: 'image' | 'video'
}

export interface PlayerSettings {
	mode: DisplayMode
	artLyrics: boolean
	background: PlayerBackground
	brightness: number
	volume: number
}

const STORAGE_KEY = 'lithium-player-settings'

const defaults: PlayerSettings = {
	mode: 'lyrics',
	artLyrics: false,
	background: { source: 'cover', url: null, type: 'image' },
	brightness: 1,
	volume: 1
}

function load(): PlayerSettings {
	if (!browser) return defaults
	try {
		const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}')
		return {
			...defaults,
			...saved,
			background: { ...defaults.background, ...saved.background }
		}
	} catch {
		return defaults
	}
}

function createPlayerSettings() {
	const store = writable<PlayerSettings>(load())
	store.subscribe((value) => {
		if (!browser) return
		try {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
		} catch {}
	})
	return {
		...store,
		patch: (partial: Partial<PlayerSettings>) => store.update((s) => ({ ...s, ...partial }))
	}
}

export const playerSettings = createPlayerSettings()

export function resolveBackgroundUrl(url: string): string {
	return url.startsWith('/background/') ? `${APIUrl}${url}` : url
}

export function guessMediaType(url: string): 'image' | 'video' {
	return /\.(mp4|webm|mov|m4v)(\?|#|$)/i.test(url) ? 'video' : 'image'
}
