import { Bookmark, GitCompare, ExternalLink, Sparkles } from "lucide-react";
import { Link } from "@tanstack/react-router";

export interface Repo {
  slug: string;
  name: string;
  description: string;
  tags: string[];
  match: number;
  health: string;
  rationale: string;
}

export function RepoCard({ repo }: { repo: Repo }) {
  const matchColor =
    repo.match >= 90
      ? "text-accent bg-accent/10"
      : repo.match >= 75
      ? "text-emerald-300 bg-emerald-400/10"
      : "text-zinc-300 bg-zinc-400/10";

  return (
    <div className="group bg-surface ring-1 ring-white/5 rounded-xl p-5 hover:ring-white/10 transition-shadow flex flex-col">
      <div className="flex items-start justify-between mb-4 gap-4">
        <div className="min-w-0">
          <h3 className="text-base font-semibold truncate">{repo.name}</h3>
          <p className="text-sm text-muted-foreground text-pretty mt-1 line-clamp-2">
            {repo.description}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className={`text-xs font-mono px-2 py-0.5 rounded ${matchColor}`}>
            {repo.match}% Match
          </span>
          <span className="text-[10px] text-muted-foreground uppercase tracking-tighter font-mono">
            Health: {repo.health}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-5">
        {repo.tags.map((t) => (
          <span
            key={t}
            className="text-[10px] font-mono px-2 py-0.5 rounded bg-secondary text-zinc-300"
          >
            {t}
          </span>
        ))}
      </div>

      <div className="bg-canvas/60 rounded-lg p-3 border border-border mb-5">
        <div className="flex items-center gap-1.5 mb-1">
          <Sparkles className="size-3 text-accent" />
          <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">
            Why this matched
          </span>
        </div>
        <p className="text-xs text-zinc-400 leading-relaxed">{repo.rationale}</p>
      </div>

      <div className="flex items-center gap-2 mt-auto">
        <Link
          to="/repo/$slug"
          params={{ slug: repo.slug }}
          className="flex-1 bg-foreground text-background text-sm font-medium py-2 rounded-md hover:bg-foreground/90 transition-colors text-center inline-flex items-center justify-center gap-1.5"
        >
          View Repo <ExternalLink className="size-3.5" />
        </Link>
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
