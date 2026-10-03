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
