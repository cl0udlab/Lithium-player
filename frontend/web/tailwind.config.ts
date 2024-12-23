import type { Config } from 'tailwindcss';
import disyui from 'daisyui';

export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],

	theme: {
		extend: {}
	},

	plugins: [disyui],
	daisyui: {
		themes: ['light', 'dark']
	}
} satisfies Config;
