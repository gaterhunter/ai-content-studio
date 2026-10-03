"use client";

import { useState } from "react";
import type { Draft, DraftEdit, PublishJob } from "@/lib/types";

const ISSUE_LABELS: Record<string, string> = {
  hua_hen_tai_chinh: "Hứa hẹn tài chính quá mức",
  suc_khoe: "Tuyên bố sức khỏe cần thận trọng",
  tuyet_doi_hoa: "Lời tuyệt đối hóa",
  chu_de_cam: "Chạm chủ đề bạn đã cấm",
  can_dan_nguon: "Nên dẫn nguồn",
  thieu_nhan_quang_cao: "Thiếu nhãn quảng cáo/affiliate",
};

const STATUS_LABEL = { draft: "Nháp", approved: "Đã duyệt", rejected: "Đã loại" } as const;

interface Props {
  draft: Draft;
  job: PublishJob | undefined;
  busy: boolean;
  onEdit: (id: number, body: DraftEdit) => Promise<void>;
  onApprove: (id: number) => Promise<void>;
  onPosted: (job: PublishJob, url: string) => Promise<void>;
}

export default function DraftCard({ draft, job, busy, onEdit, onApprove, onPosted }: Props) {
  const [editing, setEditing] = useState(false);
  const [caption, setCaption] = useState(draft.caption);
  const [hook, setHook] = useState(draft.hook);
  const [postUrl, setPostUrl] = useState("");
  const blocked = draft.compliance.issues.some((i) => i.severity === "high");
  const posted = job?.status === "posted";
  const locked = draft.review_status !== "draft";

  async function save() {
    await onEdit(draft.id, { caption, hook });
    setEditing(false);
  }

  return (
    <article className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 space-y-4">
      <header className="flex flex-wrap items-center gap-2 text-sm">
        <span className="font-medium">Phương án {draft.variant}</span>
        <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--muted)]">
          Điểm giọng {Math.round(draft.voice_score * 100)}%
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            posted ? "bg-green-600/15 text-green-700 dark:text-green-400"
            : draft.review_status === "approved" ? "bg-blue-600/15 text-blue-700 dark:text-blue-400"
            : "bg-stone-500/15 text-[var(--muted)]"
          }`}
        >
          {posted ? "Đã đăng" : STATUS_LABEL[draft.review_status]}
        </span>
        {draft.edited && <span className="text-xs text-[var(--muted)]">đã sửa</span>}
      </header>

      <section>
        <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Hook 3 giây đầu</p>
        {editing ? (
          <textarea className="mt-1 w-full rounded-lg border border-[var(--border)] bg-transparent p-2 text-sm"
            rows={2} value={hook} onChange={(e) => setHook(e.target.value)} />
        ) : (
          <p className="mt-1 font-medium">{draft.hook}</p>
        )}
      </section>

      <section>
        <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Kịch bản</p>
        <ol className="mt-1 space-y-2 text-sm">
          {draft.script.map((s, i) => (
            <li key={i} className="grid grid-cols-[4.5rem_1fr] gap-2">
              <span className="text-[var(--muted)]">{s.t}</span>
              <span>
                {s.line}
                <span className="block text-xs text-[var(--muted)]">Cảnh: {s.visual}</span>
              </span>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Caption</p>
        {editing ? (
          <textarea className="mt-1 w-full rounded-lg border border-[var(--border)] bg-transparent p-2 text-sm"
            rows={3} value={caption} onChange={(e) => setCaption(e.target.value)} />
        ) : (
          <p className="mt-1 text-sm">{draft.caption}</p>
        )}
        <p className="mt-2 text-sm text-[var(--accent)]">{draft.hashtags.join(" ")}</p>
        <p className="mt-2 text-sm"><span className="text-[var(--muted)]">CTA: </span>{draft.cta}</p>
      </section>

      <details className="text-sm">
        <summary className="cursor-pointer text-[var(--muted)]">Bài dài</summary>
        <p className="mt-2 whitespace-pre-line">{draft.long_post}</p>
      </details>

      {(draft.compliance.issues.length > 0 || draft.compliance.voice_notes) && (
        <section className="space-y-1 text-sm" aria-label="Cảnh báo">
          {draft.compliance.issues.map((i, k) => (
            <p key={k} className={i.severity === "high" ? "text-red-600 dark:text-red-400" : "text-amber-600 dark:text-amber-400"}>
              {i.severity === "high" ? "Cần sửa: " : "Lưu ý: "}
              {ISSUE_LABELS[i.type] ?? i.type}{i.match ? ` (“${i.match}”)` : ""}
            </p>
          ))}
          {draft.compliance.voice_notes && (
            <p className="text-[var(--muted)]">Gợi ý giọng: {draft.compliance.voice_notes}</p>
          )}
        </section>
      )}

      <footer className="flex flex-wrap items-center gap-2">
        {!locked && (editing ? (
          <>
            <button className="btn-primary" disabled={busy} onClick={save}>Lưu sửa</button>
            <button className="btn" onClick={() => setEditing(false)}>Huỷ</button>
          </>
        ) : (
          <>
            <button className="btn-primary" disabled={busy || blocked} onClick={() => onApprove(draft.id)}
              title={blocked ? "Sửa lỗi mức cao trước khi duyệt" : undefined}>
              Duyệt và lên lịch
            </button>
            <button className="btn" onClick={() => setEditing(true)}>Sửa nhanh</button>
          </>
        ))}
        {draft.review_status === "approved" && job && !posted && (
          <>
            <input className="min-w-0 flex-1 rounded-lg border border-[var(--border)] bg-transparent px-2 py-1.5 text-sm"
              placeholder="Link bài đã đăng (không bắt buộc)" value={postUrl} onChange={(e) => setPostUrl(e.target.value)} />
            <button className="btn-primary" disabled={busy} onClick={() => onPosted(job, postUrl)}>Đã đăng</button>
          </>
        )}
        {posted && job?.post_url && (
          <a className="text-sm text-[var(--accent)] underline" href={job.post_url} target="_blank" rel="noreferrer">Xem bài</a>
        )}
      </footer>
    </article>
  );
}
