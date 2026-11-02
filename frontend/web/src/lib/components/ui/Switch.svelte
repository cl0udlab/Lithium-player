<script lang="ts">
	import { Toggle } from 'melt/builders'

	let {
		checked = $bindable(false),
		disabled = false,
		label
	}: { checked?: boolean; disabled?: boolean; label?: string } = $props()

	const toggle = new Toggle({
		value: () => checked,
		onValueChange: (v) => (checked = v),
		disabled: () => disabled
	})
</script>

<button
	{...toggle.trigger}
	role="switch"
	aria-checked={toggle.value}
	aria-label={label}
	class="relative h-6 w-11 shrink-0 rounded-full bg-surface-3 transition-colors data-[checked]:bg-accent disabled:opacity-40"
>
	<span
		class="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform {toggle.value
			? 'translate-x-5'
			: ''}"
	></span>
</button>
