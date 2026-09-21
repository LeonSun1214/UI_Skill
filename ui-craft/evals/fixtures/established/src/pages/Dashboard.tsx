import { PageHeader } from "../components/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

const stats = [
  { label: "本月收入", value: "¥ 48,200", note: "较上月 +12%" },
  { label: "待收款", value: "¥ 9,860", note: "3 张发票" },
  { label: "已开发票", value: "27", note: "本月" },
];

const invoices = [
  ["INV-0027", "北山设计", "¥ 3,200"],
  ["INV-0026", "Lumen 咖啡", "¥ 1,480"],
  ["INV-0025", "陈氏律所", "¥ 5,180"],
];

export function Dashboard() {
  return (
    <>
      <PageHeader title="总览" description="过去 30 天的账务概况。" action={<Button>新建发票</Button>} />
      <div className="grid gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <Card key={s.label}>
            <p className="text-sm text-muted">{s.label}</p>
            <p className="mt-1 font-display text-2xl tabular-nums">{s.value}</p>
            <p className="mt-1 text-sm text-muted">{s.note}</p>
          </Card>
        ))}
      </div>
      <Card title="最近发票" className="mt-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-muted">
              <th className="py-2 font-medium">编号</th>
              <th className="py-2 font-medium">客户</th>
              <th className="py-2 text-right font-medium">金额</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(([number, client, amount]) => (
              <tr key={number} className="border-b border-line last:border-b-0">
                <td className="py-3 font-mono text-xs">{number}</td>
                <td className="py-3">{client}</td>
                <td className="py-3 text-right tabular-nums">{amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
