import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, params }) => {
	const response = await fetch(`http://localhost:8000/file/album?album_id=${params.albumid}`);
	const album = await response.json();
	return { album };
};
