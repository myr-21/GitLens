import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { RepoCard } from "@/components/RepoCard";
import { repos } from "@/lib/repos";
import { Flame, Sparkles, GraduationCap, Rocket } from "lucide-react";

export const Route = createFileRoute("/discover")({
  component: Discover,
  head: () => ({ meta: [{ title: "Discover — GitSuggest" }] }),
});

const sections = [
  { title: "Trending this week", icon: Flame, slice: [0, 3] as const, hint: "Surging in developer interest" },
  { title: "Hidden gems", icon: Sparkles, slice: [2, 5] as const, hint: "High quality, low visibility" },
  { title: "Beginner friendly", icon: GraduationCap, slice: [1, 4] as const, hint: "Great onboarding & docs" },
  { title: "Production ready", icon: Rocket, slice: [0, 4] as const, hint: "Battle-tested at scale" },
];

function Discover() {
  return (
    <AppShell>
      <div className="max-w-6xl mx-auto w-full px-8 py-12 space-y-14">
        <header className="animate-fade-up">
          <h1 className="text-3xl font-semibold tracking-tight">Discover</h1>
          <p className="text-muted-foreground mt-2 max-w-xl">
            Curated repositories handpicked by the intelligence layer — sorted by relevance to your stack and recent searches.
          </p>
        </header>

        {sections.map((s, i) => {
          const Icon = s.icon;
          return (
            <section key={s.title} className="animate-fade-up" style={{ animationDelay: `${i * 80}ms` }}>
              <div className="flex items-end justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="size-8 rounded-lg bg-accent/10 ring-1 ring-accent/30 grid place-items-center">
                    <Icon className="size-4 text-accent" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold">{s.title}</h2>
                    <p className="text-xs text-muted-foreground">{s.hint}</p>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {repos.slice(s.slice[0], s.slice[1]).map((r) => (
                  <RepoCard key={r.slug} repo={r} />
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </AppShell>
  );
}
