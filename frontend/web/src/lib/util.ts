export function setCookie(name: string, value: string, days = 7) {
	const date = new Date();
	date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
	const expires = `; expires=${date.toUTCString()}`;
	document.cookie = `${name}=${value}${expires}; path=/; SameSite=Lax`;
}

