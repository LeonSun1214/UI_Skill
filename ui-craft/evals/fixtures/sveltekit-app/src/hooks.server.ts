import { redirect, type Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	const session = event.cookies.get('session');
	event.locals.user = session ? { name: 'Ada' } : null;
	if (event.url.pathname.startsWith('/settings') && !event.locals.user) {
		redirect(303, '/pricing');
	}
	return resolve(event);
};
