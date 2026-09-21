import { NavLink, Outlet } from "react-router-dom";

const nav = [
  { to: "/", label: "总览", end: true },
  { to: "/settings/profile", label: "个人资料", end: false },
];

export function AppShell() {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded-md focus:bg-panel focus:px-4 focus:py-2"
      >
        跳到主要内容
      </a>
      <aside className="border-b border-line bg-panel lg:border-r lg:border-b-0">
        <div className="flex items-center gap-2 px-5 py-4">
          <span aria-hidden="true" className="h-6 w-6 rounded-sm bg-brand" />
          <span className="font-display text-lg">Maple Books</span>
        </div>
        <nav aria-label="主导航" className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:pb-0">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex min-h-11 items-center rounded-md px-3 text-sm font-medium whitespace-nowrap transition-colors duration-200 ${
                  isActive ? "bg-brand-soft text-brand-strong" : "text-muted hover:bg-surface hover:text-ink"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main id="main" className="mx-auto w-full max-w-3xl px-5 py-8 lg:px-10 lg:py-12">
        <Outlet />
      </main>
    </div>
  );
}
