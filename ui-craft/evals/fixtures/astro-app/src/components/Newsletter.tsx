import { useState } from 'react';

interface NewsletterProps {
	heading: string;
	cta?: string;
}

export default function Newsletter({ heading, cta = 'Subscribe' }: NewsletterProps) {
	const [email, setEmail] = useState('');
	return (
		<form className="newsletter" onSubmit={(e) => e.preventDefault()}>
			<h2>{heading}</h2>
			<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} aria-label="Email" />
			<button type="submit">{cta}</button>
		</form>
	);
}
