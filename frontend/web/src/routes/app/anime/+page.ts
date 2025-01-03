import { APIUrl } from '$lib/api';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
    const response = await fetch(`${APIUrl}/video/anime`);
    const animes = await response.json();
    return {
        animes
    };
}) satisfies PageLoad;