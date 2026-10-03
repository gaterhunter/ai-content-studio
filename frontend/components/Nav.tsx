"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Hôm nay" },
  { href: "/trends", label: "Trend" },
  { href: "/onboarding", label: "Tạo persona" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <nav className="border-b border-[var(--border)]">
      <div className="mx-auto flex max-w-3xl items-center gap-1 px-4 py-2 text-sm">
        <span className="mr-3 font-semibold">AI Content Studio</span>
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href}
            className={`rounded-lg px-3 py-1.5 ${path === l.href ? "bg-[var(--accent)] text-white" : "text-[var(--muted)] hover:bg-stone-500/10"}`}>
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
