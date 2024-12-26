import type { Config } from 'tailwindcss'
import disyui from 'daisyui'
import vidstack from 'vidstack/tailwind.cjs'

export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],

	theme: {
		extend: {}
	},

	plugins: [disyui, vidstack],
	daisyui: {
		themes: ['light', 'dark']
	}
} satisfies Config
