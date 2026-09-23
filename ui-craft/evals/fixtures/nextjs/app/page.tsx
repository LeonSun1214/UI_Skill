import Link from "next/link";

const stats = [
  { label: "本月收入", value: "¥ 48,200", note: "较上月 +12%" },
  { label: "待收款", value: "¥ 9,860", note: "3 张发票" },
  { label: "已开发票", value: "27", note: "本月" },
];

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <header className="flex items-end justify-between border-b border-line pb-6">
        <div>
          <h1 className="font-[family-name:var(--font-display)] text-3xl font-medium">总览</h1>
          <p className="mt-1 text-sm text-muted">过去 30 天的账务概况。</p>
        </div>
        <Link href="/invoices/new" className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 text-sm font-medium text-brand-fg transition-colors hover:bg-brand-strong">
          新建发票
        </Link>
      </header>
      <section aria-label="关键指标" className="mt-8 grid gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <div key={s.label} className="rounded-md border border-line bg-panel p-4">
            <p className="text-sm text-muted">{s.label}</p>
            <p className="mt-1 text-2xl font-medium tabular-nums">{s.value}</p>
            <p className="mt-1 text-sm text-muted">{s.note}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
