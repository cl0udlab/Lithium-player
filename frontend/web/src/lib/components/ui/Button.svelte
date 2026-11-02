<script lang="ts">
	import type { Snippet } from 'svelte'
	import type { HTMLAnchorAttributes, HTMLButtonAttributes } from 'svelte/elements'

	type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
	type Size = 'sm' | 'md' | 'lg' | 'icon' | 'icon-sm'

	type Props = {
		variant?: Variant
		size?: Size
		href?: string
		class?: string
		children?: Snippet
	} & HTMLButtonAttributes &
		HTMLAnchorAttributes

	let {
		variant = 'secondary',
		size = 'md',
		href,
		class: className = '',
		children,
		type = 'button',
		...rest
	}: Props = $props()

	const variants: Record<Variant, string> = {
		primary: 'bg-accent text-accent-fg hover:bg-accent-hover',
		secondary: 'bg-surface-2 text-fg hover:bg-surface-3 border border-line/10',
		ghost: 'text-fg-muted hover:bg-line/5 hover:text-fg',
		danger: 'bg-danger/15 text-danger hover:bg-danger/25'
	}
	const sizes: Record<Size, string> = {
		sm: 'h-8 gap-1.5 rounded-lg px-3 text-xs',
		md: 'h-10 gap-2 rounded-lg px-4 text-sm',
		lg: 'h-12 gap-2 rounded-xl px-6 text-base',
		icon: 'h-10 w-10 rounded-full',
		'icon-sm': 'h-8 w-8 rounded-full'
	}

	const classes = $derived(
		`inline-flex shrink-0 select-none items-center justify-center font-medium transition-all active:scale-[0.97] disabled:pointer-events-none disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`
	)
</script>

{#if href}
	<a {href} class={classes} {...rest}>{@render children?.()}</a>
{:else}
	<button {type} class={classes} {...rest}>{@render children?.()}</button>
{/if}
