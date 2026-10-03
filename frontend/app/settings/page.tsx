"use client";

import { useCallback, useEffect, useState } from "react";
import ProviderCard from "@/components/ProviderCard";
import { api, usingMock } from "@/lib/api";
import type { AppSettings, KeyProvider } from "@/lib/types";

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setSettings(await api.settings());
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function run(fn: () => Promise<AppSettings>) {
    setBusy(true);
    try {
      setSettings(await fn());
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const providers: KeyProvider[] = ["gemini", "anthropic"];

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">Cài đặt AI</h1>
        <p className="text-sm text-[var(--muted)]">
          Chọn nhà cung cấp AI viết nội dung và dán API key của bạn. Key được mã hoá trước khi lưu và không bao giờ hiển thị lại đầy đủ.
        </p>
        {usingMock && <p className="text-sm text-amber-600">Đang dùng dữ liệu mẫu, key chưa được lưu thật.</p>}
        {error && <p role="alert" className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm">{error}</p>}
      </header>

      {settings && (
        <>
          <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <h2 className="font-medium">Nhà cung cấp đang dùng</h2>
            <div className="mt-2 flex flex-wrap gap-2">
              <button className={settings.provider === "mock" ? "btn-primary" : "btn"} disabled={busy}
                onClick={() => run(() => api.setProvider("mock"))}>Dữ liệu mẫu (không cần key)</button>
              {providers.map((p) => (
                <button key={p} className={settings.provider === p ? "btn-primary" : "btn"}
                  disabled={busy || !settings.providers[p].configured}
                  title={settings.providers[p].configured ? undefined : "Lưu key trước"}
                  onClick={() => run(() => api.setProvider(p))}>
                  {p === "gemini" ? "Gemini" : "Claude"}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-[var(--muted)]">
              Chế độ dữ liệu mẫu chỉ sinh nội dung khung để thử giao diện. Chuyển sang Gemini hoặc Claude để có nội dung thật.
            </p>
          </section>

          {providers.map((p) => (
            <ProviderCard key={p} provider={p} status={settings.providers[p]} active={settings.provider === p}
              canStore={settings.can_store_keys} busy={busy}
              onSave={(key) => run(() => api.saveKey(p, key))}
              onDelete={() => run(() => api.deleteKey(p))}
              onUse={() => run(() => api.setProvider(p))}
              onTest={() => api.testKey(p)} />
          ))}

          <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm">
            Lưu ý bảo mật: ứng dụng chưa có đăng nhập, nên ai mở được địa chỉ web này đều đổi được key và dùng hạn mức của bạn.
            Chỉ dùng cho bản thử riêng tư cho tới khi có đăng nhập.
          </p>
        </>
      )}
    </main>
  );
}
