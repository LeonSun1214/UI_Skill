export const load = async ({ fetch }) => {
	const res = await fetch('/api/reports');
	return { stats: await res.json() };
};
