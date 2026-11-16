const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')

function fixture(fetchCache = async () => ({ ok: true })) {
	const tracks = [], errors = []
	const modules = {
		'svelte/store': { writable(initial) {
			let value = initial
			const listeners = []
			return {
				subscribe(fn) { listeners.push(fn); fn(value) },
				update(fn) { value = fn(value); listeners.forEach(listener => listener(value)) }
			}
		} },
		'$lib/types': { isStreamTrack: track => track?.kind === 'stream', trackKey: track => `${track.kind ?? 'music'}-${track.id}` },
		'$lib/stores/playerlist': { playerliststat: {
			addmusic(track) { tracks.push(track) }, gettracks: () => tracks,
			resetlist() { tracks.length = 0 }
		} },
		'$lib/api': { APIUrl: '/api', apiFetch: fetchCache },
		'$lib/stores/toast.svelte': { toast: { error: message => errors.push(message) } }
	}
	const source = fs.readFileSync(path.join(__dirname, '../src/lib/stores/player.ts'), 'utf8')
	const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
	const exports = {}
	vm.runInNewContext(js, { exports, require: name => modules[name], setTimeout, clearTimeout,
		fetch: async () => ({ ok: false }), console: { error() {} } })
	class Audio extends EventTarget {
		currentTime = 0
		paused = true
		error = null
		value = ''
		autoReady = true
		plays = 0
		set src(value) { this.value = value; if (this.autoReady) queueMicrotask(() => this.dispatchEvent(new Event('canplay'))) }
		get src() { return this.value }
		getAttribute() { return this.value || null }
		removeAttribute() { this.value = '' }
		load() {}
		pause() { this.paused = true }
		async play() { this.paused = false; this.plays++ }
	}
	const player = new Audio(), store = exports.playerState
	let state
	store.subscribe(value => { state = value })
	store.setPlayer(player)
	return { player, store, errors, state: () => state }
}

const song = id => ({ id, kind: 'stream', url: `subsonic://source/${id}`, title: `Song ${id}`, artist: 'Artist', lyrics: '' })

test('empty queue does not change or start the player', async () => {
	const f = fixture()
	await f.store.playMusiclist([])
	assert.equal(f.player.plays, 0)
	assert.equal(f.state().currentTrack, null)
})

test('cache failure clears previous audio and retry plays the selected track', async () => {
	let offline = false
	const f = fixture(async () => ({ ok: !offline, json: async () => ({ detail: 'offline' }) }))
	await f.store.playMusic(song(1))
	offline = true
	await f.store.playMusic(song(2))
	assert.equal(f.player.src, '')
	assert.equal(f.state().isPlaying, false)
	assert.equal(f.errors[0], 'offline')
	offline = false
	await f.store.togglePlayback()
	assert.equal(f.player.src, '/api/stream/stream/2')
	assert.equal(f.state().isPlaying, true)
})

test('late cache completion cannot replace a newer selection', async () => {
	let finish
	const f = fixture(url => url.endsWith('/1') ? new Promise(resolve => { finish = resolve }) : Promise.resolve({ ok: true }))
	const pending = f.store.playMusic(song(1))
	await f.store.playMusic(song(2))
	finish({ ok: true })
	await pending
	assert.equal(f.player.src, '/api/stream/stream/2')
	assert.equal(f.player.plays, 1)
})

test('stop cancels pending loading and prevents late autoplay', async () => {
	let finish
	const f = fixture(() => new Promise(resolve => { finish = resolve }))
	const pending = f.store.playMusic(song(1))
	f.store.stop()
	finish({ ok: true })
	await pending
	assert.equal(f.player.plays, 0)
	assert.equal(f.state().isPlaying, false)
})

test('media load error settles playback and a new track still plays', async () => {
	const f = fixture()
	f.player.autoReady = false
	const pending = f.store.playMusic({ ...song(1), url: 'https://other.example/song' })
	f.player.dispatchEvent(new Event('error'))
	await pending
	assert.equal(f.state().isPlaying, false)
	assert.equal(f.errors.length, 1)
	f.player.autoReady = true
	await f.store.playMusic(song(2))
	assert.equal(f.state().isPlaying, true)
})
