import { json } from '@sveltejs/kit';

export const GET = () => json([{ label: 'Revenue', value: '$12k', delta: 4 }]);
