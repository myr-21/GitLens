import { Bookmark, GitCompare, ExternalLink, Sparkles, Star, Clock } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { formatStars, formatCommitDate, toMatchPercent, type RepoSuggestion } from "@/lib/api";

// ── Legacy mock-data shape (kept for "Recommended for your stack" section) ───
export interface Repo {
  slug: string;
  name: string;
  description: string;
  tags: string[];
  match: number;
  health: string;
  rationale: string;
}

// ── Convert a live API suggestion into the card's unified props ──────────────
export interface RepoCardProps {
  // live API result
  suggestion?: RepoSuggestion;
  // static mock (home page featured section)
  repo?: Repo;
}

export function RepoCard({ suggestion, repo }: RepoCardProps) {
  // Normalise either shape into a common display model
  const name = suggestion ? suggestion.repo : (repo?.name ?? "");
  const description = suggestion
    ? suggestion.use_case_fit
    : (repo?.description ?? "");
  const rationale = suggestion ? suggestion.why : (repo?.rationale ?? "");
  const matchPct = suggestion
    ? toMatchPercent(suggestion.relevance_score)
    : (repo?.match ?? 0);
  const tags = suggestion
    ? [suggestion.repo.split("/")[1]] // derive tag from "owner/name"
    : (repo?.tags ?? []);
  const stars = suggestion ? suggestion.stars : null;
  const lastCommit = suggestion ? suggestion.last_commit : null;
  const ghUrl = suggestion
    ? `https://github.com/${suggestion.repo}`
    : null;
  // slug for internal route — use repo name part
  const slug = suggestion
    ? suggestion.repo.replace("/", "--")
    : (repo?.slug ?? "");

  const matchColor =
    matchPct >= 90
      ? "text-accent bg-accent/10"
      : matchPct >= 70
      ? "text-emerald-300 bg-emerald-400/10"
      : "text-zinc-300 bg-zinc-400/10";

  return (
    <div className="group bg-surface ring-1 ring-white/5 rounded-xl p-5 hover:ring-white/10 transition-shadow flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between mb-4 gap-4">
        <div className="min-w-0">
          <h3 className="text-base font-semibold truncate font-mono">{name}</h3>
          <p className="text-sm text-muted-foreground text-pretty mt-1 line-clamp-2">
            {description}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className={`text-xs font-mono px-2 py-0.5 rounded ${matchColor}`}>
            {matchPct}% Match
          </span>
          {repo && (
            <span className="text-[10px] text-muted-foreground uppercase tracking-tighter font-mono">
              Health: {repo.health}
            </span>
          )}
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {tags.map((t) => (
          <span
            key={t}
            className="text-[10px] font-mono px-2 py-0.5 rounded bg-secondary text-zinc-300"
          >
            {t}
          </span>
        ))}
      </div>

      {/* Live meta row (stars + last commit) */}
      {suggestion && (stars !== null || lastCommit) && (
        <div className="flex items-center gap-4 mb-4 text-[11px] text-muted-foreground font-mono">
          {stars !== null && (
            <span className="flex items-center gap-1">
              <Star className="size-3 text-yellow-400" />
              {formatStars(stars)}
            </span>
          )}
          {lastCommit && (
            <span className="flex items-center gap-1">
              <Clock className="size-3" />
              {formatCommitDate(lastCommit)}
            </span>
          )}
        </div>
      )}

      {/* Rationale box */}
      <div className="bg-canvas/60 rounded-lg p-3 border border-border mb-5">
        <div className="flex items-center gap-1.5 mb-1">
          <Sparkles className="size-3 text-accent" />
          <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">
            Why this matched
          </span>
        </div>
        <p className="text-xs text-zinc-400 leading-relaxed">{rationale}</p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 mt-auto">
        {ghUrl ? (
          <a
            href={ghUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 bg-foreground text-background text-sm font-medium py-2 rounded-md hover:bg-foreground/90 transition-colors text-center inline-flex items-center justify-center gap-1.5"
          >
            View on GitHub <ExternalLink className="size-3.5" />
          </a>
        ) : (
          <Link
            to="/repo/$slug"
            params={{ slug }}
            className="flex-1 bg-foreground text-background text-sm font-medium py-2 rounded-md hover:bg-foreground/90 transition-colors text-center inline-flex items-center justify-center gap-1.5"
          >
            View Repo <ExternalLink className="size-3.5" />
          </Link>
        )}
        <button className="py-2 px-3 bg-secondary text-zinc-300 text-sm rounded-md border border-border hover:bg-secondary/70 transition-colors inline-flex items-center gap-1.5">
          <GitCompare className="size-3.5" /> Compare
        </button>
        <button
          className="p-2 bg-secondary text-zinc-300 rounded-md border border-border hover:bg-secondary/70 transition-colors"
          aria-label="Save"
        >
          <Bookmark className="size-4" />
        </button>
      </div>
    </div>
  );
}
