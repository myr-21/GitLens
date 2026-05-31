import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { repos } from "@/lib/repos";
import { Sparkles, X } from "lucide-react";

export const Route = createFileRoute("/compare")({
  component: Compare,
  head: () => ({ meta: [{ title: "Compare — GitSuggest" }] }),
});

const metrics = [
  { key: "Match", get: (r: typeof repos[number]) => `${r.match}%` },
  { key: "Health", get: (r: typeof repos[number]) => r.health },
  { key: "Primary language", get: (r: typeof repos[number]) => r.tags[0] },
  { key: "Tech stack", get: (r: typeof repos[number]) => r.tags.join(" · ") },
  { key: "Description", get: (r: typeof repos[number]) => r.description },
];

function Compare() {
  const items = repos.slice(0, 3);
  return (
    <AppShell>
      <div className="max-w-6xl mx-auto w-full px-8 py-12 space-y-10">
        <header className="animate-fade-up">
          <h1 className="text-3xl font-semibold tracking-tight">Compare</h1>
          <p className="text-muted-foreground mt-2 max-w-xl">
            Side-by-side analysis with an AI summary explaining what truly sets them apart.
          </p>
        </header>

        <div className="bg-surface ring-1 ring-white/5 rounded-2xl p-6 animate-fade-up">
          <div className="flex items-center gap-2 mb-3">
            <div className="size-7 rounded-md bg-accent/15 ring-1 ring-accent/30 grid place-items-center">
              <Sparkles className="size-3.5 text-accent" />
            </div>
            <h3 className="text-sm font-semibold">AI Summary</h3>
            <span className="text-[10px] font-mono uppercase text-muted-foreground tracking-widest ml-1">
              auto-generated
            </span>
          </div>
          <p className="text-sm text-zinc-300 leading-relaxed">
            <span className="text-accent font-medium">{items[0].name}</span> wins on community velocity and integration breadth, while{" "}
            <span className="text-accent font-medium">{items[1].name}</span> is the safer pick for end-to-end typesafety. If you need the lowest operational overhead,{" "}
            <span className="text-accent font-medium">{items[2].name}</span> scales to zero and gives the cleanest cost profile.
          </p>
        </div>

        <div className="bg-surface ring-1 ring-white/5 rounded-2xl overflow-hidden animate-fade-up">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-canvas/40">
                <tr>
                  <th className="text-left p-4 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground w-44">
                    Metric
                  </th>
                  {items.map((r) => (
                    <th key={r.slug} className="text-left p-4 font-semibold">
                      <div className="flex items-start justify-between gap-2">
                        <span>{r.name}</span>
                        <button className="text-muted-foreground hover:text-foreground" aria-label="Remove">
                          <X className="size-4" />
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.map((m) => (
                  <tr key={m.key} className="border-t border-border">
                    <td className="p-4 text-xs text-muted-foreground font-mono uppercase tracking-wider">
                      {m.key}
                    </td>
                    {items.map((r) => (
                      <td key={r.slug} className="p-4 align-top text-zinc-200">
                        {m.get(r)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-up">
          {items.map((r) => (
            <div key={r.slug} className="bg-surface ring-1 ring-white/5 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-muted-foreground font-mono uppercase tracking-widest">
                  Velocity
                </span>
                <span className="text-xs font-mono text-accent">{r.match}%</span>
              </div>
              <div className="h-2 bg-canvas/60 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-accent/70 to-accent rounded-full"
                  style={{ width: `${r.match}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-3">{r.name}</p>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
