import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const display = Fraunces({ subsets: ["latin"], variable: "--font-display", display: "swap" });
const body = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-body", display: "swap" });

export const metadata: Metadata = { title: "Maple Books", description: "Invoices for small studios" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${display.variable} ${body.variable}`}>
      <body className="min-h-screen font-[family-name:var(--font-body)]">{children}</body>
    </html>
  );
}
