import { fail } from '@sveltejs/kit';

export const actions = {
	default: async ({ request }) => {
		const data = await request.formData();
		if (!data.get('email')) return fail(400, { error: 'Email is required.' });
		return { ok: true };
	}
};
