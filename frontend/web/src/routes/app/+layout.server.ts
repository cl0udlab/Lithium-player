import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies }) => {
	const isExpandedCookie = cookies.get('isExpanded');
	const isExpanded = isExpandedCookie === 'false' ? false : true;

	return { isExpanded };
};
