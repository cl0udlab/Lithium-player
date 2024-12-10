import type { Config } from 'tailwindcss'
import disyui from 'daisyui'

export default {
	content: [
        './src/**/*.{html,js,svelte,ts}',
        '/frontend/desktop/src/**/*.{html,js,svelte,ts}'
    ],

	theme: {
		extend: {}
	},

	plugins: [disyui],
	daisyui: {
		themes: true
	}
} satisfies Config
