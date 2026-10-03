export type Platform = "tiktok" | "reels" | "shorts" | "facebook";
export type ReviewStatus = "draft" | "approved" | "rejected";
export type PublishStatus = "scheduled" | "posted" | "skipped";

export interface Persona {
  id: number;
  name: string;
  niche: string;
  revenue_goal: string;
  platforms: string[];
}

export interface ComplianceIssue {
  type: string;
  match: string;
  severity: "high" | "medium";
}

export interface Compliance {
  ok: boolean;
  issues: ComplianceIssue[];
  disclosure_required: boolean;
  voice_notes?: string;
  reminders?: string[];
}

export interface ScriptLine {
  t: string;
  line: string;
  visual: string;
}

export interface Draft {
  id: number;
  platform: Platform;
  variant: number;
  hook: string;
  script: ScriptLine[];
  long_post: string;
  caption: string;
  hashtags: string[];
  cta: string;
  voice_score: number;
  compliance: Compliance;
  review_status: ReviewStatus;
  edited: boolean;
}

export type DraftEdit = Partial<Pick<Draft, "hook" | "long_post" | "caption" | "hashtags" | "cta">>;

export interface Idea {
  id: number;
  title: string;
  angle: string;
  reason: string;
  funnel_stage: "attract" | "trust" | "sell";
  planned_for: string | null;
}

export interface PackItem {
  platform: Platform;
  suggested_time: string;
  drafts: Draft[];
}

export interface DailyPack {
  date: string;
  idea: Idea | null;
  items: PackItem[];
}

export interface PublishJob {
  id: number;
  content_id: number;
  platform: Platform;
  scheduled_at: string;
  status: PublishStatus;
  post_url: string | null;
}

export interface PersonaInput {
  user_id: number;
  name: string;
  niche: string;
  revenue_goal: "ads" | "affiliate" | "course" | "brand_deal";
  platforms: Platform[];
  questionnaire: {
    audience: string;
    tone: string;
    banned_topics: string[];
    catchphrases: string[];
  };
  sample_posts: string[];
}

export interface TrendInput {
  platform: Platform;
  title: string;
  kind: "sound" | "format" | "topic" | "keyword";
  description: string;
  popularity: number;
  estimated_expiry?: string | null;
}

export interface RankedTrend {
  id: number;
  title: string;
  kind: string;
  platform: string;
  fit: number;
  risk: "low" | "medium" | "high";
  note: string;
  days_left: number;
  score: number;
}

export type LlmProvider = "mock" | "gemini" | "anthropic";
export type KeyProvider = "gemini" | "anthropic";

export interface ProviderStatus {
  configured: boolean;
  source: "settings" | "env" | null;
  masked: string | null;
  error: string | null;
  writer_model: string;
  fast_model: string;
}

export interface AppSettings {
  provider: LlmProvider;
  providers: Record<KeyProvider, ProviderStatus>;
  can_store_keys: boolean;
}

export interface TestResult {
  ok: boolean;
  provider: string;
  message: string;
}
