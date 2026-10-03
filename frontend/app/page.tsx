"use client";

import { useCallback, useEffect, useState } from "react";
import DraftCard from "@/components/DraftCard";
import { api, usingMock } from "@/lib/api";
import type { DailyPack, DraftEdit, Persona, Platform, PublishJob } from "@/lib/types";

const PLATFORM_LABEL: Record<Platform, string> = {
  tiktok: "TikTok", reels: "Reels", shorts: "Shorts", facebook: "Facebook",
};
const STAGE_LABEL = { attract: "Thu hút", trust: "Tin tưởng", sell: "Bán" } as const;

const todayStr = () => new Date().toLocaleDateString("sv-SE"); // YYYY-MM-DD theo giờ máy

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("vi-VN", { weekday: "short", hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" });
}

export default function Home() {
  const [userId, setUserId] = useState(1);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [personaId, setPersonaId] = useState<number | null>(null);
  const [day, setDay] = useState(todayStr());
  const [pack, setPack] = useState<DailyPack | null>(null);
  const [jobs, setJobs] = useState<PublishJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const saved = Number(localStorage.getItem("acs:userId"));
      if (saved > 0) setUserId(saved);
    } catch {}
  }, []);

  useEffect(() => {
    let cancelled = false;
    api.personas(userId)
      .then((list) => {
        if (cancelled) return;
        setPersonas(list);
        setPersonaId(list[0]?.id ?? null);
        setError(null);
      })
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => { cancelled = true; };
  }, [userId]);

  const load = useCallback(async () => {
    if (personaId == null) { setPack(null); return; }
    setLoading(true);
    try {
      const [p, j] = await Promise.all([api.dailyPack(personaId, day), api.jobs(personaId)]);
      setPack(p);
      setJobs(j);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [personaId, day]);

  useEffect(() => { load(); }, [load]);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    try {
      await fn();
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const edit = (id: number, body: DraftEdit) => run(() => api.edit(id, body));
  const approve = (id: number) => run(() => api.approve(id, null));
  const posted = (job: PublishJob, url: string) => run(() => api.markPosted(job.id, url.trim() || null));
  const jobOf = (contentId: number) => jobs.find((j) => j.content_id === contentId);

  const totalItems = pack?.items.length ?? 0;
  const doneItems = pack?.items.filter((it) => it.drafts.some((d) => jobOf(d.id)?.status === "posted")).length ?? 0;

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 space-y-6">
      <header className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Gói nội dung hôm nay</h1>
            <p className="text-sm text-[var(--muted)]">Chọn phương án, sửa nhanh, duyệt rồi đăng.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <label className="flex items-center gap-1">
              <span className="text-[var(--muted)]">Người dùng</span>
              <input type="number" min={1} value={userId} disabled={usingMock}
                className="w-16 rounded-lg border border-[var(--border)] bg-transparent px-2 py-1"
                onChange={(e) => {
                  const v = Math.max(1, Number(e.target.value) || 1);
                  setUserId(v);
                  try { localStorage.setItem("acs:userId", String(v)); } catch {}
                }} />
            </label>
            <select aria-label="Persona" className="rounded-lg border border-[var(--border)] bg-transparent px-2 py-1"
              value={personaId ?? ""} onChange={(e) => setPersonaId(Number(e.target.value))}>
              {personas.length === 0 && <option value="">Chưa có persona</option>}
              {personas.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <input type="date" aria-label="Ngày" value={day} onChange={(e) => setDay(e.target.value)}
              className="rounded-lg border border-[var(--border)] bg-transparent px-2 py-1" />
          </div>
        </div>
        {usingMock && (
          <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm">
            Đang dùng dữ liệu mẫu. Đặt <code>NEXT_PUBLIC_API_BASE_URL</code> để nối backend thật.
          </p>
        )}
        {error && (
          <p role="alert" className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm">{error}</p>
        )}
      </header>

      {loading && !pack && <p className="text-sm text-[var(--muted)]">Đang tải…</p>}

      {pack && !pack.idea && (
        <p className="rounded-xl border border-dashed border-[var(--border)] p-6 text-sm text-[var(--muted)]">
          Chưa có ý tưởng nào cho ngày này.
        </p>
      )}

      {pack?.idea && (
        <>
          <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
              Ý tưởng · {STAGE_LABEL[pack.idea.funnel_stage]} · đã đăng {doneItems}/{totalItems} nền tảng
            </p>
            <h2 className="mt-1 text-lg font-medium">{pack.idea.title}</h2>
            <p className="mt-1 text-sm">{pack.idea.angle}</p>
            <p className="mt-1 text-sm text-[var(--muted)]">Lý do: {pack.idea.reason}</p>
          </section>

          {pack.items.map((item) => (
            <section key={item.platform} className="space-y-3">
              <div className="flex items-baseline justify-between">
                <h3 className="text-lg font-medium">{PLATFORM_LABEL[item.platform]}</h3>
                <p className="text-sm text-[var(--muted)]">Giờ đăng gợi ý: {formatTime(item.suggested_time)}</p>
              </div>
              <div className="space-y-3">
                {item.drafts.map((d) => (
                  <DraftCard key={`${d.id}-${d.edited}`} draft={d} job={jobOf(d.id)} busy={busy}
                    onEdit={edit} onApprove={approve} onPosted={posted} />
                ))}
              </div>
            </section>
          ))}
        </>
      )}
    </main>
  );
}
