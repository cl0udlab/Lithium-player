export interface LyricLine {
	time: number
	text: string
	translations: string[]
}

const TIME_TAG = /\[(\d{1,3}):(\d{1,2}(?:[.:]\d{1,3})?)\]/g

export function parseLyrics(lyricsText: string): LyricLine[] {
	const entries: { time: number; text: string; order: number }[] = []
	lyricsText.split('\n').forEach((line, order) => {
		const tags = [...line.matchAll(TIME_TAG)]
		if (tags.length === 0) return
		const text = line.replace(TIME_TAG, '').trim()
		for (const tag of tags) {
			const seconds = parseFloat(tag[2].replace(':', '.'))
			entries.push({ time: parseInt(tag[1]) * 60 + seconds, text, order })
		}
	})
	entries.sort((a, b) => a.time - b.time || a.order - b.order)

	const lines: LyricLine[] = []
	for (const entry of entries) {
		const last = lines[lines.length - 1]
		if (last && Math.abs(last.time - entry.time) < 0.01) {
			if (entry.text) last.translations.push(entry.text)
			continue
		}
		lines.push({ time: entry.time, text: entry.text, translations: [] })
	}
	return lines
}

export function currentLyricIndex(lines: LyricLine[], currentTime: number): number {
	let index = -1
	for (let i = 0; i < lines.length; i++) {
		if (lines[i].time > currentTime) break
		index = i
	}
	return index
}
