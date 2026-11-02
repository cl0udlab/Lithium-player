export function formatTime(seconds: number): string {
	if (!Number.isFinite(seconds) || seconds < 0) seconds = 0
	const m = Math.floor(seconds / 60)
	const s = Math.floor(seconds % 60)
	return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}
