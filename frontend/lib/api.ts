import { mock } from "./mock";
import type { DailyPack, Draft, DraftEdit, Persona, PersonaInput, PublishJob, RankedTrend, TrendInput } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

export const usingMock = BASE === "";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

const json = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const api = {
  ensureUser: (email: string, name: string): Promise<{ id: number }> =>
    usingMock ? Promise.resolve({ id: 1 }) : http("/users", json({ email, name })),
  createPersona: (input: PersonaInput): Promise<Persona> =>
    usingMock ? mock.createPersona(input) : http("/personas", json(input)),
  addTrends: async (items: TrendInput[]): Promise<number> =>
    usingMock ? mock.addTrends(items) : (await http<unknown[]>("/trends", json(items))).length,
  rankedTrends: (personaId: number): Promise<RankedTrend[]> =>
    usingMock ? mock.trends() : http(`/personas/${personaId}/trends`),
  personas: (userId: number): Promise<Persona[]> =>
    usingMock ? mock.personas() : http(`/personas?user_id=${userId}`),
  dailyPack: (personaId: number, day: string): Promise<DailyPack> =>
    usingMock ? mock.pack(day) : http(`/personas/${personaId}/daily-pack?day=${day}`),
  jobs: (personaId: number): Promise<PublishJob[]> =>
    usingMock ? mock.jobs() : http(`/personas/${personaId}/calendar`),
  edit: (id: number, body: DraftEdit): Promise<Draft> =>
    usingMock ? mock.edit(id, body) : http(`/contents/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  approve: (id: number, scheduledAt: string | null): Promise<PublishJob> =>
    usingMock ? mock.approve(id, scheduledAt) : http(`/contents/${id}/approve`, json({ scheduled_at: scheduledAt })),
  markPosted: (jobId: number, postUrl: string | null): Promise<PublishJob> =>
    usingMock ? mock.posted(jobId, postUrl) : http(`/publish-jobs/${jobId}/posted`, json({ post_url: postUrl })),
};
