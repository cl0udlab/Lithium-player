<script lang="ts">
	import { Slider } from 'melt/builders'

	let {
		value = $bindable(0),
		min = 0,
		max = 1,
		step = 0.01,
		label,
		onchange,
		class: className = ''
	}: {
		value?: number
		min?: number
		max?: number
		step?: number
		label?: string
		onchange?: (value: number) => void
		class?: string
	} = $props()

	const slider = new Slider({
		value: () => value,
		onValueChange: (v) => {
			value = v
			onchange?.(v)
		},
		min: () => min,
		max: () => max,
		step: () => step
	})
</script>

<div
	{...slider.root}
	aria-label={label}
	class="group relative flex h-4 w-full cursor-pointer items-center outline-hidden {className}"
>
	<div class="h-1 w-full overflow-hidden rounded-full bg-line/15">
		<div class="h-full bg-fg group-hover:bg-accent" style="width: var(--percentage)"></div>
	</div>
	<div
		{...slider.thumb}
		class="absolute h-3 w-3 -translate-x-1/2 rounded-full bg-white opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100 data-[dragging]:opacity-100"
		style="left: var(--percentage)"
	></div>
</div>
