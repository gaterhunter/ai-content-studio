"use client";

import { useState } from "react";
import type { KeyProvider, ProviderStatus, TestResult } from "@/lib/types";

interface Guide {
  name: string;
  url: string;
  urlLabel: string;
  placeholder: string;
  steps: string[];
  note: string;
}

export const GUIDES: Record<KeyProvider, Guide> = {
  gemini: {
    name: "Google Gemini",
    url: "https://aistudio.google.com/apikey",
    urlLabel: "aistudio.google.com/apikey",
    placeholder: "AIza…",
    steps: [
      "Mở trang lấy key và đăng nhập bằng tài khoản Google.",
      "Bấm “Create API key”. Nếu được hỏi, chọn một project Google Cloud có sẵn hoặc để Google tạo project mới.",
      "Copy chuỗi key (bắt đầu bằng AIza…) rồi dán vào ô bên dưới.",
      "Bấm Lưu, sau đó bấm “Thử kết nối” để kiểm tra.",
    ],
    note: "Gemini có gói miễn phí giới hạn số lượt gọi mỗi phút/ngày; hết hạn mức app sẽ báo lỗi và bạn thử lại sau, hoặc bật thanh toán trong Google AI Studio.",
  },
  anthropic: {
    name: "Claude (Anthropic)",
    url: "https://console.anthropic.com/settings/keys",
    urlLabel: "console.anthropic.com/settings/keys",
    placeholder: "sk-ant-…",
    steps: [
      "Mở trang lấy key và đăng nhập (hoặc đăng ký) tài khoản Anthropic Console.",
      "Nạp một ít credit ở mục Billing, vì key mới chưa có credit sẽ không gọi được.",
      "Bấm “Create Key”, đặt tên bất kỳ, rồi copy key (bắt đầu bằng sk-ant-…). Key chỉ hiện một lần.",
      "Dán vào ô bên dưới, bấm Lưu rồi “Thử kết nối”.",
    ],
    note: "Claude tính tiền theo lượng chữ xử lý (xem bảng giá hiện hành trên trang Anthropic); hết credit thì app sẽ báo lỗi cho tới khi bạn nạp thêm.",
  },
};

interface Props {
  provider: KeyProvider;
  status: ProviderStatus;
  active: boolean;
  canStore: boolean;
  busy: boolean;
  onSave: (key: string) => Promise<void>;
  onDelete: () => Promise<void>;
  onTest: () => Promise<TestResult>;
  onUse: () => Promise<void>;
}

export default function ProviderCard({ provider, status, active, canStore, busy, onSave, onDelete, onTest, onUse }: Props) {
  const g = GUIDES[provider];
  const [key, setKey] = useState("");
  const [show, setShow] = useState(false);
  const [result, setResult] = useState<TestResult | null>(null);
  const [testing, setTesting] = useState(false);

  async function save() {
    await onSave(key.trim());
    setKey("");
    setResult(null);
  }

  async function test() {
    setTesting(true);
    try {
      setResult(await onTest());
    } finally {
      setTesting(false);
    }
  }

  return (
    <section className="space-y-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-medium">{g.name}</h2>
          <p className="text-sm text-[var(--muted)]">
            Mô hình viết: {status.writer_model} · lọc trend: {status.fast_model}
          </p>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-xs ${active ? "bg-green-600/15 text-green-700 dark:text-green-400" : "bg-stone-500/15 text-[var(--muted)]"}`}>
          {active ? "Đang dùng" : status.configured ? "Đã có key" : "Chưa có key"}
        </span>
      </header>

      {status.error && <p role="alert" className="text-sm text-red-600">{status.error}</p>}

      {status.configured && (
        <p className="text-sm">
          Key hiện tại: <code>{status.masked}</code>{" "}
          <span className="text-[var(--muted)]">
            ({status.source === "env" ? "lấy từ biến môi trường của server, nhập key mới ở đây sẽ được ưu tiên" : "đã lưu mã hoá trên server"})
          </span>
        </p>
      )}

      <details className="rounded-lg border border-[var(--border)] p-3 text-sm" open={!status.configured}>
        <summary className="cursor-pointer font-medium">Cách lấy API key {g.name}</summary>
        <ol className="mt-2 list-decimal space-y-1 pl-5">
          {g.steps.map((s, i) => <li key={i}>{s}</li>)}
        </ol>
        <p className="mt-2">
          Link: <a className="text-[var(--accent)] underline" href={g.url} target="_blank" rel="noreferrer">{g.urlLabel}</a>
        </p>
        <p className="mt-2 text-[var(--muted)]">{g.note}</p>
      </details>

      <div className="space-y-2">
        <label className="block text-sm font-medium" htmlFor={`key-${provider}`}>
          {status.configured ? "Thay bằng key mới" : "Dán API key"}
        </label>
        <div className="flex gap-2">
          <input id={`key-${provider}`} type={show ? "text" : "password"} autoComplete="off" spellCheck={false}
            className="min-w-0 flex-1 rounded-lg border border-[var(--border)] bg-transparent px-2 py-1.5 text-sm"
            placeholder={g.placeholder} value={key} onChange={(e) => setKey(e.target.value)} />
          <button type="button" className="btn" onClick={() => setShow(!show)}>{show ? "Ẩn" : "Hiện"}</button>
        </div>
        {!canStore && (
          <p className="text-sm text-amber-600">
            Server chưa đặt <code>TOKEN_ENCRYPTION_KEY</code> nên chưa lưu được key qua giao diện. Hãy đặt biến này (xem README) hoặc đặt <code>{provider === "gemini" ? "GEMINI_API_KEY" : "ANTHROPIC_API_KEY"}</code> trực tiếp trên server.
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button className="btn-primary" disabled={busy || !canStore || key.trim().length < 8} onClick={save}>Lưu key</button>
        <button className="btn" disabled={busy || testing || !status.configured} onClick={test}>
          {testing ? "Đang thử…" : "Thử kết nối"}
        </button>
        <button className="btn" disabled={busy || !status.configured || active} onClick={onUse}>Dùng nhà cung cấp này</button>
        {status.source === "settings" && (
          <button className="btn" disabled={busy} onClick={onDelete}>Xoá key</button>
        )}
      </div>

      {result && (
        <p role="status" className={`text-sm ${result.ok ? "text-green-700 dark:text-green-400" : "text-red-600"}`}>
          {result.ok ? "✓ " : "✗ "}{result.message}
        </p>
      )}
    </section>
  );
}
