const API_BASE = "http://localhost:8000";

// ── Types matching the backend Pydantic models ────────────────────────────────

export interface RepoSuggestion {
  rank: number;
  repo: string;          // "owner/name"
  relevance_score: number;
  why: string;
  use_case_fit: string;
  stars: number;
  last_commit: string;   // ISO date string
}

export interface SuggestResponse {
  intent_summary: string;
  suggestions: RepoSuggestion[];
  follow_up_question: string | null;
}

export interface SuggestRequest {
  description: string;
  language?: string | null;
  limit?: number;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export async function fetchSuggestions(req: SuggestRequest): Promise<SuggestResponse> {
  const res = await fetch(`${API_BASE}/suggest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<SuggestResponse>;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Convert relevance_score (0–1) to a percentage integer. */
export function toMatchPercent(score: number): number {
  return Math.round(score * 100);
}

/** Format ISO date to "MMM YYYY" or "N days ago". */
export function formatCommitDate(iso: string): string {
  if (!iso) return "Unknown";
  try {
    const d = new Date(iso);
    const diffDays = Math.floor((Date.now() - d.getTime()) / 86_400_000);
    if (diffDays < 1) return "Today";
    if (diffDays < 7) return `${diffDays}d ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
    return `${Math.floor(diffDays / 365)}y ago`;
  } catch {
    return iso;
  }
}

/** Format star count: 103252 → "103.3k" */
export function formatStars(n: number): string {
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}
