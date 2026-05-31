import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { RepoCard } from "@/components/RepoCard";
import { repos } from "@/lib/repos";
import { Search, ArrowUpRight } from "lucide-react";
import { useState } from "react";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "GitSuggest — Find the perfect architecture" },
      { name: "description", content: "Intelligent GitHub repository discovery for builders. Search projects, tech stacks, or ideas." },
    ],
  }),
});

const suggestions = ["MERN ecommerce", "Spring Boot JWT auth", "AI chatbot", "Redis caching"];

function Index() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");

  const submit = (query: string) => {
    if (!query.trim()) return;
    navigate({ to: "/results", search: { q: query } });
  };

  return (
    <AppShell>
      <section className="w-full max-w-4xl mx-auto px-8 pt-24 pb-12 flex flex-col items-center animate-fade-up">
        <div className="mb-6 inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/20 bg-accent/5 text-[11px] font-medium text-accent uppercase tracking-wider font-mono">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-60"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
          </span>
          Intelligent Discovery
        </div>

        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-balance text-center mb-10 leading-[1.1]">
          Find the perfect architecture
          <br className="hidden sm:block" />
          <span className="text-muted-foreground">for your next implementation.</span>
        </h1>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(q);
          }}
          className="w-full relative group"
        >
          <div className="absolute -inset-1 bg-accent/10 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
          <div className="relative flex items-center">
            <Search className="absolute left-5 size-5 text-muted-foreground/60 pointer-events-none" />
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search projects, tech stacks, or ideas…"
              className="w-full bg-surface border border-border rounded-2xl py-5 pl-14 pr-32 text-lg outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent/40 transition-all placeholder:text-muted-foreground/50"
            />
            <div className="absolute right-3 flex items-center gap-2">
              <kbd className="hidden sm:inline-flex items-center h-6 px-1.5 font-mono text-[10px] font-medium text-muted-foreground bg-secondary border border-border rounded">
                ⌘ K
              </kbd>
              <button
                type="submit"
                className="bg-foreground text-background text-sm font-medium px-4 py-2 rounded-lg hover:bg-foreground/90 transition-colors inline-flex items-center gap-1"
              >
                Search <ArrowUpRight className="size-3.5" />
              </button>
            </div>
          </div>
        </form>

        <div className="flex flex-wrap justify-center gap-2 mt-6">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => submit(s)}
              className="text-xs px-3 py-1.5 rounded-full bg-surface border border-border text-muted-foreground hover:text-foreground hover:border-accent/40 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      </section>

      <section className="w-full max-w-5xl mx-auto px-8 pb-20 animate-fade-up [animation-delay:120ms]">
        <div className="flex items-center justify-between mb-6 gap-6">
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-widest whitespace-nowrap">
            Recommended for your stack
          </h2>
          <div className="h-px flex-1 bg-border" />
          <Link to="/discover" className="text-xs text-accent hover:underline whitespace-nowrap">
            View all →
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {repos.slice(0, 4).map((r) => (
            <RepoCard key={r.slug} repo={r} />
          ))}
        </div>
      </section>
    </AppShell>
  );
}
