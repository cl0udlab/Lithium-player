import { sveltekit } from '@sveltejs/kit/vite'
import { vite as vidstack } from 'vidstack/plugins'
import { defineConfig } from 'vite'

export default defineConfig({
	plugins: [vidstack(), sveltekit()],
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api/, '')
			}
		}
	}
})
