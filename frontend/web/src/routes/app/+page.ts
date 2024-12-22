import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	try {
		const response = await fetch('http://localhost:8000/file/music');

		if (!response.ok) {
			return {
				musics: [],
				error: `載入失敗: ${response.statusText}`,
				status: response.status
			};
		}

		const musics = await response.json();
    console.log(musics);
		return {
			musics,
			error: null,
			status: 200
		};
	} catch (e) {
    console.error(e);
		return {
			musics: [],
			error: '無法連接到伺服器',
			status: 500
		};
	}
}) satisfies PageLoad;
