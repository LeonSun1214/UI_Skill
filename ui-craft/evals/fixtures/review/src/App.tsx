import { useState } from "react";

// 等位通 · 商家后台 · 今日排队
// A working page with the kind of problems a busy team ships: it renders fine, it just
// isn't finished. (Test fixture for the review/fix path — see fixtures/README.md.)

type Status = "waiting" | "called" | "seated" | "cancelled";

type Ticket = {
  no: string;
  name: string;
  party: number;
  phone: string;
  joined: string;
  waited: string;
  status: Status;
  note: string;
};

const STATUS_COLOR: Record<Status, string> = {
  waiting: "bg-amber-400",
  called: "bg-blue-500",
  seated: "bg-emerald-500",
  cancelled: "bg-gray-300",
};

const TICKETS: Ticket[] = [
  { no: "A032", name: "王先生", party: 4, phone: "138****2041", joined: "18:02", waited: "23 分钟", status: "waiting", note: "靠窗" },
  { no: "A031", name: "李女士", party: 2, phone: "150****8817", joined: "17:58", waited: "27 分钟", status: "called", note: "" },
  { no: "A030", name: "张总", party: 6, phone: "139****0906", joined: "17:51", waited: "—", status: "seated", note: "包间" },
  { no: "A029", name: "陈先生", party: 3, phone: "186****3320", joined: "17:47", waited: "—", status: "seated", note: "" },
  { no: "A028", name: "赵女士", party: 2, phone: "137****5512", joined: "17:40", waited: "—", status: "cancelled", note: "电话未接" },
  { no: "B012", name: "周先生", party: 8, phone: "135****7791", joined: "17:36", waited: "49 分钟", status: "waiting", note: "有儿童" },
];

function IconButton({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  // 20×20, no accessible name, no visible focus, no hover change
  return (
    <button type="button" onClick={onClick} className="h-5 w-5 rounded text-gray-500 focus:outline-none">
      {children}
    </button>
  );
}

export default function App() {
  const [tickets, setTickets] = useState(TICKETS);
  const call = (no: string) => setTickets((t) => t.map((x) => (x.no === no ? { ...x, status: "called" } : x)));
  const remove = (no: string) => setTickets((t) => t.filter((x) => x.no !== no));
  const waiting = tickets.filter((t) => t.status === "waiting").length;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <img src="data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32'%3E%3Crect width='32' height='32' rx='6' fill='%230f172a'/%3E%3Ctext x='16' y='21' font-size='14' text-anchor='middle' fill='%23fff' font-family='sans-serif'%3E%E7%AD%89%3C/text%3E%3C/svg%3E" className="h-8 w-8 rounded" />
            <span className="font-semibold">等位通 · 商家后台</span>
          </div>
          <nav className="flex gap-6 text-sm">
            <a href="#queue" className="text-gray-600 hover:text-gray-900 focus:outline-none">排队</a>
            <a href="#tables" className="text-gray-600 hover:text-gray-900 focus:outline-none">桌位</a>
            <a href="#stats" className="text-gray-600 hover:text-gray-900 focus:outline-none">报表</a>
            <a href="#settings" className="text-gray-600 hover:text-gray-900 focus:outline-none">设置</a>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-2xl font-semibold">今日排队</h1>
            <p className="mt-1 text-sm text-gray-400">2026-09-25 · 晚市 · 最近更新 18:25</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
            实时同步中
          </div>
        </div>

        <section id="stats" className="mt-6 grid grid-cols-3 gap-4">
          {[
            ["等位中", String(waiting), "组"],
            ["平均等待", "31", "分钟"],
            ["今日已入座", "128", "组"],
          ].map(([label, value, unit]) => (
            <div key={label} className="rounded-lg border border-gray-200 bg-white p-4">
              <p className="text-xs text-gray-400">{label}</p>
              <p className="mt-1 text-2xl font-semibold">
                {value} <span className="text-sm font-normal text-gray-400">{unit}</span>
              </p>
            </div>
          ))}
        </section>

        <section id="queue" className="mt-8">
          <h3 className="text-lg font-semibold">排队列表</h3>
          <p className="mt-1 text-sm text-gray-400">点击叫号会向顾客发送短信；删除不可撤销。</p>

          <table className="mt-4 w-full border-collapse bg-white text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-400">
                <th className="px-3 py-2 font-medium">号码</th>
                <th className="px-3 py-2 font-medium">顾客</th>
                <th className="px-3 py-2 font-medium">人数</th>
                <th className="px-3 py-2 font-medium">手机</th>
                <th className="px-3 py-2 font-medium">取号时间</th>
                <th className="px-3 py-2 font-medium">已等待</th>
                <th className="px-3 py-2 font-medium">备注</th>
                <th className="px-3 py-2 font-medium">状态</th>
                <th className="px-3 py-2 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.no} className="border-b border-gray-100">
                  <td className="whitespace-nowrap px-3 py-2 font-mono">{t.no}</td>
                  <td className="whitespace-nowrap px-3 py-2">{t.name}</td>
                  <td className="whitespace-nowrap px-3 py-2">{t.party}</td>
                  <td className="whitespace-nowrap px-3 py-2 text-gray-400">{t.phone}</td>
                  <td className="whitespace-nowrap px-3 py-2 text-gray-400">{t.joined}</td>
                  <td className="whitespace-nowrap px-3 py-2">{t.waited}</td>
                  <td className="whitespace-nowrap px-3 py-2 text-gray-400">{t.note || "—"}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${STATUS_COLOR[t.status]}`} />
                  </td>
                  <td className="whitespace-nowrap px-3 py-2">
                    <div className="flex items-center gap-2">
                      <IconButton onClick={() => call(t.no)}>
                        <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5"><path d="M4 3h3l1.5 4-2 1.2a11 11 0 0 0 5.3 5.3L13 11.5l4 1.5v3a1 1 0 0 1-1 1A13 13 0 0 1 3 4a1 1 0 0 1 1-1Z" /></svg>
                      </IconButton>
                      <IconButton onClick={() => remove(t.no)}>
                        <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5"><path d="M6 6h8l-.7 10H6.7L6 6Zm1-3h6l1 2H6l1-2Z" /></svg>
                      </IconButton>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section id="tables" className="mt-10">
          <h3 className="text-lg font-semibold">桌位</h3>
          <p className="mt-1 text-sm text-gray-400">大厅 12 桌 · 包间 3 间 · 当前空桌 2</p>
          <div className="mt-4 flex gap-3">
            <button type="button" className="rounded-md bg-gray-900 px-4 py-2 text-sm text-white hover:bg-gray-700">刷新桌位</button>
            <button type="button" className="rounded-md border border-gray-200 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">导出今日记录</button>
          </div>
        </section>
      </main>
    </div>
  );
}
