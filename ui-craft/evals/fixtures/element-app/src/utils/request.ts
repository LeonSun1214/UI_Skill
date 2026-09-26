export default function request(opts: { url: string; method: string }) {
  return fetch('/dev-api' + opts.url, { method: opts.method }).then((r) => r.json());
}
