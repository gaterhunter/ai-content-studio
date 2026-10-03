import type { AppSettings, DailyPack, Draft, DraftEdit, KeyProvider, LlmProvider, Persona, PersonaInput, PublishJob, RankedTrend, TestResult, TrendInput } from "./types";

export const mockPersona: Persona = {
  id: 1,
  name: "Hyu dạy Excel",
  niche: "excel kế toán",
  revenue_goal: "course",
  platforms: ["tiktok", "reels"],
};

function draft(id: number, platform: "tiktok" | "reels", variant: number, hook: string, score: number): Draft {
  return {
    id,
    platform,
    variant,
    hook,
    script: [
      { t: "0-3s", line: hook, visual: "Cận mặt, nhìn thẳng camera" },
      { t: "3-15s", line: "Mình từng mất 2 tiếng mỗi ngày chỉ để đối chiếu số liệu bằng tay.", visual: "Cảnh thật trên màn hình Excel" },
      { t: "15-40s", line: "Ba hàm này giúp mình làm trong 5 phút: XLOOKUP, SUMIFS, và Pivot Table.", visual: "Chữ hiện từng ý trên màn hình" },
      { t: "40-50s", line: "Lưu video lại, comment hàm bạn muốn mình hướng dẫn tiếp.", visual: "Quay lại cận mặt, chỉ tay vào nút lưu" },
    ],
    long_post: `${hook}\n\nMình làm kế toán 6 năm và từng nghĩ Excel là việc của dân IT. Hóa ra ba hàm cơ bản đã tiết kiệm cho mình hơn 10 tiếng mỗi tuần.\n\nLưu lại để dùng khi cần nhé.`,
    caption: "3 hàm Excel kế toán nào cũng nên biết. Lưu lại dùng dần nhé!",
    hashtags: ["#excel", "#ketoan", "#hoctrentiktok", "#meoexcel", "#chiase"],
    cta: "Lưu lại và comment hàm bạn muốn học tiếp.",
    voice_score: score,
    compliance: { ok: true, issues: [], disclosure_required: false, voice_notes: "Thêm một con số thật từ công việc của bạn." },
    review_status: "draft",
    edited: false,
  };
}

let drafts: Draft[] = [];
let jobs: PublishJob[] = [];

export function resetMock() {
  drafts = [
    draft(1, "tiktok", 1, "Đừng mất 2 tiếng mỗi ngày cho việc Excel này!", 0.86),
    draft(2, "tiktok", 2, "3 giây thôi: kế toán nào cũng sai chỗ này.", 0.74),
    draft(3, "reels", 1, "Mình đã sai về Excel suốt 6 năm.", 0.81),
    draft(4, "reels", 2, "Đây là hàm Excel mình ước biết sớm hơn.", 0.69),
  ];
  jobs = [];
}
resetMock();

const delay = <T,>(v: T) => new Promise<T>((r) => setTimeout(() => r(v), 150));

let trends: RankedTrend[] = [
  { id: 1, title: "Mẹo excel 1 phút", kind: "format", platform: "tiktok", fit: 0.9, risk: "low", note: "Khớp niche", days_left: 9, score: 0.82 },
];

const emptyStatus = (w: string, f: string) => ({ configured: false, source: null, masked: null, error: null, writer_model: w, fast_model: f });
const settings: AppSettings = {
  provider: "mock",
  providers: { gemini: emptyStatus("gemini-2.5-pro", "gemini-2.5-flash"), anthropic: emptyStatus("claude-opus-5-5", "claude-haiku-4-5") },
  can_store_keys: true,
};
const snap = (): AppSettings => JSON.parse(JSON.stringify(settings));

export const mock = {
  settings: () => delay(snap()),
  setProvider: (p: LlmProvider) => { settings.provider = p; return delay(snap()); },
  saveKey: (p: KeyProvider, key: string) => {
    Object.assign(settings.providers[p], { configured: true, source: "settings", masked: `••••${key.slice(-4)}` });
    return delay(snap());
  },
  deleteKey: (p: KeyProvider) => {
    Object.assign(settings.providers[p], { configured: false, source: null, masked: null });
    if (settings.provider === p) settings.provider = "mock";
    return delay(snap());
  },
  testKey: (p: KeyProvider): Promise<TestResult> =>
    delay({ ok: settings.providers[p].configured, provider: p, message: settings.providers[p].configured ? "Kết nối thành công (dữ liệu mẫu)" : "Chưa có API key" }),
  createPersona: (input: PersonaInput) => {
    mockPersona.name = input.name;
    mockPersona.niche = input.niche;
    return delay({ ...mockPersona });
  },
  addTrends: (items: TrendInput[]) => {
    items.forEach((t) =>
      trends.push({ id: trends.length + 1, title: t.title, kind: t.kind, platform: t.platform, fit: 0.7,
        risk: "low", note: "Điểm mẫu", days_left: 7, score: 0.6 }));
    return delay(items.length);
  },
  trends: () => delay([...trends].sort((a, b) => b.score - a.score)),
  personas: () => delay([mockPersona]),
  pack: (day: string): Promise<DailyPack> =>
    delay({
      date: day,
      idea: {
        id: 1,
        title: "3 hàm Excel giúp kế toán tiết kiệm 10 tiếng mỗi tuần",
        angle: "Kể trải nghiệm thật khi đối chiếu số liệu thủ công",
        reason: "Bước tin tưởng, dẫn tới khóa học Excel kế toán",
        funnel_stage: "trust",
        planned_for: day,
      },
      items: (["tiktok", "reels"] as const).map((p) => ({
        platform: p,
        suggested_time: `${day}T${p === "tiktok" ? "20:00" : "19:30"}:00+07:00`,
        drafts: drafts.filter((d) => d.platform === p),
      })),
    }),
  jobs: () => delay([...jobs]),
  edit: (id: number, body: DraftEdit) => {
    const d = drafts.find((x) => x.id === id)!;
    Object.assign(d, body, { edited: true });
    return delay({ ...d });
  },
  approve: (id: number, at: string | null) => {
    const d = drafts.find((x) => x.id === id)!;
    d.review_status = "approved";
    drafts.filter((x) => x.platform === d.platform && x.id !== id && x.review_status === "draft")
      .forEach((x) => (x.review_status = "rejected"));
    const job: PublishJob = {
      id: id * 10, content_id: id, platform: d.platform, scheduled_at: at ?? new Date().toISOString(),
      status: "scheduled", post_url: null,
    };
    jobs.push(job);
    return delay(job);
  },
  posted: (jobId: number, url: string | null) => {
    const j = jobs.find((x) => x.id === jobId)!;
    j.status = "posted";
    j.post_url = url;
    return delay({ ...j });
  },
};
