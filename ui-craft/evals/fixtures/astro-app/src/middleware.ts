import { defineMiddleware } from 'astro:middleware';

export const onRequest = defineMiddleware((context, next) => {
	if (context.url.pathname.startsWith('/drafts') && !context.cookies.get('editor')) {
		return context.redirect('/');
	}
	return next();
});
