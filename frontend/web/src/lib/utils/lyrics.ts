interface LyricLine {
	time: number
	text: string
}

export function parseLyrics(lyricsText: string): LyricLine[] {
	const lines = lyricsText.split('\n')
	return lines
		.map((line) => {
			const match = line.match(/\[(\d{2}):(\d{2}\.\d{2})\](.*)/)
			if (!match) return null

			const minutes = parseInt(match[1])
			const seconds = parseFloat(match[2])
			const time = minutes * 60 + seconds
			const text = match[3].trim()

			return { time, text }
		})
		.filter((line): line is LyricLine => line !== null)
		.sort((a, b) => a.time - b.time)
}
