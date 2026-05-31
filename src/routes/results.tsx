import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { AppShell } from "@/components/AppShell";
import { RepoCard } from "@/components/RepoCard";
import { repos } from "@/lib/repos";
import { Search, SlidersHorizontal } from "lucide-react";
import { useState } from "react";

const searchSchema = z.object({
  q: fallback(z.string(), "").default(""),
});

export const Route = createFileRoute("/results")({
  validateSearch: zodValidator(searchSchema),
  component: Results,
  head: () => ({ meta: [{ title: "Results — GitSuggest" }] }),
});

const filters = [
  { label: "Language", options: ["Any", "TypeScript", "Rust", "Python", "Go"] },
  { label: "Stars", options: ["Any", "1k+", "10k+", "50k+"] },
  { label: "Activity", options: ["Any", "Active", "Maintained", "Archived"] },
  { label: "Difficulty", options: ["Any", "Beginner", "Intermediate", "Advanced"] },
  { label: "Architecture", options: ["Any", "Monolith", "Microservices", "Serverless"] },
  { label: "Updated", options: ["Any", "Past week", "Past month", "Past year"] },
];

function Results() {
  const { q } = Route.useSearch();
  const navigate = useNavigate();
  const [query, setQuery] = useState(q);

  return (
    <AppShell>
      <div className="sticky top-0 z-20 bg-canvas/85 backdrop-blur-md border-b border-border">
        <div className="max-w-6xl mx-auto px-8 py-4 flex items-center gap-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              navigate({ to: "/results", search: { q: query } });
            }}
            className="relative flex-1"
          >
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-4 text-muted-foreground/60" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search projects, tech stacks, or ideas…"
              className="w-full bg-surface border border-border rounded-lg py-2.5 pl-11 pr-4 text-sm outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/40 transition-all"
            />
          </form>
          <button className="inline-flex items-center gap-2 px-3 py-2.5 rounded-lg bg-surface border border-border text-sm text-muted-foreground hover:text-foreground transition-colors">
            <SlidersHorizontal className="size-4" /> Filters
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto w-full px-8 py-8 grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-8">
        <aside className="space-y-6">
          <div>
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-3">
              Filters
            </h3>
            <div className="space-y-5">
              {filters.map((f) => (
                <div key={f.label}>
                  <label className="text-xs font-medium text-zinc-300 block mb-2">
                    {f.label}
                  </label>
                  <select className="w-full bg-surface border border-border rounded-md px-3 py-2 text-xs text-zinc-200 outline-none focus:border-accent/40">
                    {f.options.map((o) => (
                      <option key={o}>{o}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <div>
          <div className="mb-6 flex items-baseline justify-between">
            <div>
              <h1 className="text-xl font-semibold">
                {q ? <>Results for <span className="font-mono text-accent">{q}</span></> : "All repositories"}
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                {repos.length} repositories • ranked by intelligent match
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {repos.map((r) => (
              <RepoCard key={r.slug} repo={r} />
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
