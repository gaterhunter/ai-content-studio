"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, usingMock } from "@/lib/api";
import type { Platform, PersonaInput } from "@/lib/types";

const GOALS = {
  ads: "Quảng cáo nền tảng",
  affiliate: "Affiliate / TikTok Shop",
  course: "Bán khóa học, tư vấn",
  brand_deal: "Brand deal",
} as const;
const PLATFORMS: { id: Platform; label: string }[] = [
  { id: "tiktok", label: "TikTok" }, { id: "reels", label: "Reels" },
  { id: "shorts", label: "Shorts" }, { id: "facebook", label: "Facebook" },
];

const lines = (s: string) => s.split(/\n|,/).map((x) => x.trim()).filter(Boolean);

export default function Onboarding() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [niche, setNiche] = useState("");
  const [goal, setGoal] = useState<PersonaInput["revenue_goal"]>("course");
  const [platforms, setPlatforms] = useState<Platform[]>(["tiktok", "reels"]);
  const [audience, setAudience] = useState("");
  const [tone, setTone] = useState("");
  const [banned, setBanned] = useState("");
  const [catchphrases, setCatchphrases] = useState("");
  const [posts, setPosts] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await api.ensureUser(email.trim() || "creator@example.com", name.trim());
      await api.createPersona({
        user_id: user.id, name: name.trim(), niche: niche.trim(), revenue_goal: goal, platforms,
        questionnaire: { audience, tone, banned_topics: lines(banned), catchphrases: lines(catchphrases) },
        sample_posts: posts.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean).slice(0, 5),
      });
      try { localStorage.setItem("acs:userId", String(user.id)); } catch {}
      router.push("/");
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  const field = "mt-1 w-full rounded-lg border border-[var(--border)] bg-transparent px-2 py-1.5 text-sm";
  const label = "block text-sm font-medium";
  const hint = "text-xs font-normal text-[var(--muted)]";

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <header>
        <h1 className="text-2xl font-semibold">Tạo persona</h1>
        <p className="text-sm text-[var(--muted)]">Khai báo một lần, hệ thống dùng cho mọi nội dung. Mất khoảng 10 phút.</p>
        {usingMock && <p className="mt-2 text-sm text-amber-600">Đang dùng dữ liệu mẫu, persona chưa được lưu thật.</p>}
        {error && <p role="alert" className="mt-2 text-sm text-red-600">{error}</p>}
      </header>

      <form onSubmit={submit} className="space-y-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className={label}>Email<input className={field} type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ban@example.com" /></label>
          <label className={label}>Tên persona<input className={field} required value={name} onChange={(e) => setName(e.target.value)} placeholder="Hyu dạy Excel" /></label>
        </div>
        <label className={label}>Niche<input className={field} required value={niche} onChange={(e) => setNiche(e.target.value)} placeholder="excel kế toán" /></label>
        <div>
          <p className={label}>Mục tiêu kiếm tiền</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {Object.entries(GOALS).map(([k, v]) => (
              <button type="button" key={k} onClick={() => setGoal(k as PersonaInput["revenue_goal"])}
                className={goal === k ? "btn-primary" : "btn"}>{v}</button>
            ))}
          </div>
        </div>
        <div>
          <p className={label}>Nền tảng</p>
          <div className="mt-1 flex flex-wrap gap-3 text-sm">
            {PLATFORMS.map((p) => (
              <label key={p.id} className="flex items-center gap-1">
                <input type="checkbox" checked={platforms.includes(p.id)}
                  onChange={(e) => setPlatforms(e.target.checked ? [...platforms, p.id] : platforms.filter((x) => x !== p.id))} />
                {p.label}
              </label>
            ))}
          </div>
        </div>
        <label className={label}>Khán giả của bạn<input className={field} value={audience} onChange={(e) => setAudience(e.target.value)} placeholder="nhân viên kế toán mới ra trường" /></label>
        <label className={label}>Giọng văn<input className={field} value={tone} onChange={(e) => setTone(e.target.value)} placeholder="vui, thẳng thắn, thực tế" /></label>
        <label className={label}>Chủ đề cấm <span className={hint}>(mỗi dòng hoặc ngăn cách bằng dấu phẩy)</span>
          <textarea className={field} rows={2} value={banned} onChange={(e) => setBanned(e.target.value)} /></label>
        <label className={label}>Câu cửa miệng
          <textarea className={field} rows={2} value={catchphrases} onChange={(e) => setCatchphrases(e.target.value)} placeholder="Nói thật nhé" /></label>
        <label className={label}>3 đến 5 bài cũ của bạn <span className={hint}>(cách nhau một dòng trống, để hệ thống học giọng)</span>
          <textarea className={field} rows={6} value={posts} onChange={(e) => setPosts(e.target.value)} /></label>
        <button className="btn-primary" disabled={busy || !name.trim() || !niche.trim() || platforms.length === 0}>
          {busy ? "Đang tạo…" : "Tạo persona"}
        </button>
      </form>
    </main>
  );
}
