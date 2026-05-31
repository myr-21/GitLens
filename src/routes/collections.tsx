import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { FolderHeart, Plus } from "lucide-react";

export const Route = createFileRoute("/collections")({
  component: Collections,
  head: () => ({ meta: [{ title: "Collections — GitSuggest" }] }),
});

const collections = [
  { name: "Production stack", count: 12, color: "from-accent/30 to-accent/5" },
  { name: "Learning Rust", count: 7, color: "from-orange-500/30 to-orange-500/5" },
  { name: "AI experiments", count: 24, color: "from-violet-500/30 to-violet-500/5" },
  { name: "DX tools", count: 9, color: "from-sky-500/30 to-sky-500/5" },
];

function Collections() {
  return (
    <AppShell>
      <div className="max-w-6xl mx-auto w-full px-8 py-12">
        <header className="flex items-end justify-between mb-10 animate-fade-up">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Collections</h1>
            <p className="text-muted-foreground mt-2">
              Curated buckets of repositories, organized your way.
            </p>
          </div>
          <button className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-foreground text-background text-sm font-medium hover:bg-foreground/90">
            <Plus className="size-4" /> New collection
          </button>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {collections.map((c, i) => (
            <div
              key={c.name}
              className="group relative bg-surface ring-1 ring-white/5 rounded-2xl p-6 hover:ring-white/10 cursor-pointer overflow-hidden animate-fade-up"
              style={{ animationDelay: `${i * 70}ms` }}
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${c.color} opacity-50`} />
              <div className="relative">
                <FolderHeart className="size-5 text-accent" />
                <h3 className="text-lg font-semibold mt-4">{c.name}</h3>
                <p className="text-xs text-muted-foreground mt-1 font-mono uppercase tracking-widest">
                  {c.count} repos
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
