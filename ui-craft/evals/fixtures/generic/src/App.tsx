// 等位通官网首页 — 当前版本（老板说“像模板”）。
// 任务是让它有辨识度，但保留功能与文案结构。

const features = [
  { title: "智能排队", body: "顾客扫码取号，实时查看排队进度，无需在店门口等待。" },
  { title: "实时通知", body: "快到号时通过微信自动提醒顾客，减少过号和流失。" },
  { title: "数据分析", body: "查看高峰时段、平均等待时长和翻台率，优化运营决策。" },
];

const testimonials = [
  { name: "王经理", role: "川味小馆 · 店长", quote: "用了等位通之后，高峰期门口再也不乱了，顾客也更愿意等。" },
  { name: "李女士", role: "轻食工坊 · 创始人", quote: "设置很简单，当天就上线了。过号率明显下降。" },
  { name: "张总", role: "海底捞加盟 · 区域经理", quote: "数据看板帮我们重新安排了排班，人效提升了不少。" },
];

function Icon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3l2.5 5 5.5.8-4 3.9.9 5.5L12 15.6 7.1 18.2l.9-5.5-4-3.9L9.5 8z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <span className="text-xl font-bold text-indigo-600">等位通</span>
          <nav className="hidden gap-8 text-sm text-gray-600 md:flex">
            <a href="#features">功能</a>
            <a href="#testimonials">客户评价</a>
            <a href="#pricing">定价</a>
          </nav>
          <a href="#cta" className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700">
            免费试用
          </a>
        </div>
      </header>

      <section className="relative overflow-hidden px-6 py-24 text-center">
        <div aria-hidden="true" className="absolute top-0 left-1/2 -z-10 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-gradient-to-tr from-indigo-300 via-purple-200 to-pink-200 opacity-60 blur-3xl" />
        <span className="inline-block rounded-full bg-indigo-100 px-4 py-1.5 text-sm font-medium text-indigo-700">全新 2.0 版本上线</span>
        <h1 className="mx-auto mt-6 max-w-3xl bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-5xl font-extrabold tracking-tight text-transparent md:text-6xl">
          释放您餐厅的业务潜力
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-600">
          等位通提供强大的智能排队叫号解决方案，助力餐厅提升顾客体验、优化运营效率、实现业务增长。
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <a href="#cta" className="rounded-xl bg-indigo-600 px-7 py-3.5 font-semibold text-white shadow-lg hover:bg-indigo-700">立即开始</a>
          <a href="#features" className="rounded-xl border border-gray-200 bg-white px-7 py-3.5 font-semibold text-gray-700 shadow-sm hover:bg-gray-50">了解更多</a>
        </div>
        <div className="mx-auto mt-16 max-w-4xl">
          <p className="text-sm text-gray-400">受到 500+ 家餐厅信赖</p>
          <div className="mt-6 grid grid-cols-3 gap-6 md:grid-cols-5">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 rounded-lg bg-gray-200" />
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="px-6 py-20">
        <div className="mx-auto max-w-6xl text-center">
          <h2 className="text-3xl font-bold">强大的功能</h2>
          <p className="mt-3 text-gray-500">一站式解决餐厅排队的所有问题</p>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {features.map((f) => (
              <div key={f.title} className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
                  <Icon />
                </div>
                <h3 className="mt-5 text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-gray-500">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-white px-6 py-16">
        <div className="mx-auto grid max-w-4xl gap-8 text-center sm:grid-cols-3">
          {[["10,000+", "活跃用户"], ["99.9%", "系统可用性"], ["24/7", "全天候支持"]].map(([n, l]) => (
            <div key={l}>
              <p className="text-4xl font-extrabold text-indigo-600">{n}</p>
              <p className="mt-2 text-gray-500">{l}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="testimonials" className="px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-3xl font-bold">客户怎么说</h2>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {testimonials.map((t) => (
              <div key={t.name} className="rounded-xl bg-white p-8 shadow-sm">
                <div className="text-yellow-400">★★★★★</div>
                <p className="mt-4 text-gray-600">“{t.quote}”</p>
                <div className="mt-6 flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-gray-200" />
                  <div>
                    <p className="text-sm font-semibold">{t.name}</p>
                    <p className="text-xs text-gray-400">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="pricing" className="px-6 py-20">
        <div className="mx-auto max-w-6xl text-center">
          <h2 className="text-3xl font-bold">简单透明的定价</h2>
          <div className="mt-12 grid gap-8 md:grid-cols-2">
            {[
              ["基础版", "¥ 199 / 月", ["1 家门店", "扫码取号", "微信提醒"]],
              ["专业版", "¥ 499 / 月", ["5 家门店", "数据分析", "优先支持"]],
            ].map(([name, price, items]) => (
              <div key={name as string} className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm">
                <h3 className="text-lg font-semibold">{name}</h3>
                <p className="mt-3 text-3xl font-extrabold text-indigo-600">{price}</p>
                <ul className="mt-6 space-y-2 text-sm text-gray-500">
                  {(items as string[]).map((i) => (
                    <li key={i}>✓ {i}</li>
                  ))}
                </ul>
                <a href="#cta" className="mt-8 block rounded-xl bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-700">选择方案</a>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="cta" className="px-6 py-20">
        <div className="mx-auto max-w-4xl rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 px-8 py-16 text-center text-white shadow-lg">
          <h2 className="text-3xl font-bold">准备好开始了吗？</h2>
          <p className="mt-4 text-indigo-100">立即免费试用 14 天，无需信用卡。</p>
          <a href="#" className="mt-8 inline-block rounded-xl bg-white px-8 py-3.5 font-semibold text-indigo-600 shadow-sm">免费开始</a>
        </div>
      </section>

      <footer className="border-t border-gray-200 px-6 py-8 text-center text-sm text-gray-400">© 2026 等位通 · 保留所有权利</footer>
    </div>
  );
}
