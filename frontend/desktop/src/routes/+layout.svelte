<script>
    /** @type {{ data: import('./$types').LayoutData, children: import('svelte').Snippet }} */
    import '../app.css';
    let { data, children } = $props();
</script>

{@render children()}