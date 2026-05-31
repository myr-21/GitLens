import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { repos } from "@/lib/repos";
import { Link } from "@tanstack/react-router";
import { TrendingUp } from "lucide-react";

export const Route = createFileRoute("/trending")({
  component: Trending,
  head: () => ({ meta: [{ title: "Trending — GitSuggest" }] }),
});

function Trending() {
  const ranked = [...repos].sort((a, b) => b.match - a.match);
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto w-full px-8 py-12">
        <header className="mb-8 animate-fade-up">
          <h1 className="text-3xl font-semibold tracking-tight inline-flex items-center gap-3">
            <TrendingUp className="size-7 text-accent" /> Trending
          </h1>
          <p className="text-muted-foreground mt-2">What's surging across the developer community.</p>
        </header>

        <div className="bg-surface ring-1 ring-white/5 rounded-2xl overflow-hidden">
          {ranked.map((r, i) => (
            <Link
              to="/repo/$slug"
              params={{ slug: r.slug }}
              key={r.slug}
              className="flex items-center gap-5 px-5 py-4 hover:bg-secondary/40 border-b border-border last:border-b-0 transition-colors"
            >
              <span className="text-2xl font-mono font-semibold text-muted-foreground w-8 tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div className="flex-1 min-w-0">
                <div className="font-semibold truncate">{r.name}</div>
                <div className="text-xs text-muted-foreground truncate">{r.description}</div>
              </div>
              <div className="hidden sm:flex flex-wrap gap-1.5">
                {r.tags.slice(0, 2).map((t) => (
                  <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded bg-secondary text-zinc-300">
                    {t}
                  </span>
                ))}
              </div>
              <span className="text-xs font-mono text-accent bg-accent/10 px-2 py-0.5 rounded shrink-0">
                {r.match}%
              </span>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
