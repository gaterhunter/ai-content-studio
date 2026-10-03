"use client";

import { useCallback, useEffect, useState } from "react";
import { api, usingMock } from "@/lib/api";
import { usePersona } from "@/lib/usePersona";
import type { Platform, RankedTrend, TrendInput } from "@/lib/types";

const KINDS = { format: "Định dạng", sound: "Âm thanh", topic: "Chủ đề", keyword: "Từ khóa" } as const;

export default function TrendsPage() {
  const { persona, error: personaError } = usePersona();
  const [ranked, setRanked] = useState<RankedTrend[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<TrendInput>({
    platform: "tiktok", title: "", kind: "format", description: "", popularity: 0.5, estimated_expiry: null,
  });

  const load = useCallback(async () => {
    if (!persona) return;
    try {
      setRanked(await api.rankedTrends(persona.id));
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [persona]);

  useEffect(() => { load(); }, [load]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      await api.addTrends([{ ...form, title: form.title.trim(), estimated_expiry: form.estimated_expiry || null }]);
      setForm({ ...form, title: "", description: "" });
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  const field = "w-full rounded-lg border border-[var(--border)] bg-transparent px-2 py-1.5 text-sm";

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <header>
        <h1 className="text-2xl font-semibold">Trend radar</h1>
        <p className="text-sm text-[var(--muted)]">
          Nhập trend bạn thấy, hệ thống chấm độ hợp với {persona?.name ?? "persona"} và loại trend không còn đủ ngày để quay và đăng.
        </p>
        {usingMock && <p className="mt-2 text-sm text-amber-600">Đang dùng dữ liệu mẫu.</p>}
        {(error || personaError) && <p role="alert" className="mt-2 text-sm text-red-600">{error ?? personaError}</p>}
      </header>

      <form onSubmit={submit} className="space-y-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
        <h2 className="font-medium">Thêm trend</h2>
        <input className={field} placeholder="Tên trend" value={form.title} required
          onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <textarea className={field} rows={2} placeholder="Mô tả ngắn (không bắt buộc)" value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <label className="text-xs text-[var(--muted)]">Nền tảng
            <select className={field} value={form.platform}
              onChange={(e) => setForm({ ...form, platform: e.target.value as Platform })}>
              <option value="tiktok">TikTok</option><option value="reels">Reels</option>
              <option value="shorts">Shorts</option><option value="facebook">Facebook</option>
            </select>
          </label>
          <label className="text-xs text-[var(--muted)]">Loại
            <select className={field} value={form.kind}
              onChange={(e) => setForm({ ...form, kind: e.target.value as TrendInput["kind"] })}>
              {Object.entries(KINDS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <label className="text-xs text-[var(--muted)]">Độ hot (0–1)
            <input className={field} type="number" min={0} max={1} step={0.1} value={form.popularity}
              onChange={(e) => setForm({ ...form, popularity: Math.min(1, Math.max(0, Number(e.target.value))) })} />
          </label>
          <label className="text-xs text-[var(--muted)]">Hết đà (nếu biết)
            <input className={field} type="date" value={form.estimated_expiry ?? ""}
              onChange={(e) => setForm({ ...form, estimated_expiry: e.target.value || null })} />
          </label>
        </div>
        <button className="btn-primary" disabled={saving || !form.title.trim()}>Thêm trend</button>
      </form>

      <section className="space-y-3">
        <h2 className="font-medium">Top trend hợp bạn</h2>
        {ranked.length === 0 && (
          <p className="rounded-xl border border-dashed border-[var(--border)] p-6 text-sm text-[var(--muted)]">
            Chưa có trend nào qua bộ lọc. Hãy thêm trend sát niche và còn ít nhất vài ngày.
          </p>
        )}
        {ranked.map((t) => (
          <article key={t.id} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-medium">{t.title}</h3>
              <span className="text-sm text-[var(--muted)]">
                Hợp {Math.round(t.fit * 100)}% · còn {t.days_left} ngày · rủi ro {t.risk === "low" ? "thấp" : "vừa"}
              </span>
            </div>
            <p className="mt-1 text-sm text-[var(--muted)]">{t.note}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
