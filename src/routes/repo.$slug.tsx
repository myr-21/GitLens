import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { RepoCard } from "@/components/RepoCard";
import { getRepo, repos } from "@/lib/repos";
import type { Repo } from "@/components/RepoCard";
import { ExternalLink, Bookmark, GitCompare, Activity, BookOpen, Layers, Gauge, Heart, Users } from "lucide-react";

export const Route = createFileRoute("/repo/$slug")({
  component: RepoDetail,
  loader: ({ params }) => {
    const repo = getRepo(params.slug);
    if (!repo) throw notFound();
    return { repo };
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: loaderData ? `${loaderData.repo.name} — GitSuggest` : "Repository — GitSuggest" },
      { name: "description", content: loaderData?.repo.description ?? "Repository overview" },
    ],
  }),
  notFoundComponent: () => (
    <AppShell>
      <div className="max-w-2xl mx-auto px-8 py-32 text-center">
        <h1 className="text-2xl font-semibold">Repository not found</h1>
        <Link to="/discover" className="text-accent text-sm mt-4 inline-block hover:underline">
          ← Back to Discover
        </Link>
      </div>
    </AppShell>
  ),
});

function RepoDetail() {
  const { repo } = Route.useLoaderData() as { repo: Repo };
  const similar = repos.filter((r) => r.slug !== repo.slug).slice(0, 3);

  const stats = [
    { label: "Match score", value: `${repo.match}%`, icon: Gauge },
    { label: "Health grade", value: repo.health, icon: Heart },
    { label: "Difficulty", value: "Intermediate", icon: BookOpen },
    { label: "Architecture", value: "Modular", icon: Layers },
  ];

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto w-full px-8 py-12 space-y-10">
        <header className="flex flex-col md:flex-row md:items-start md:justify-between gap-6 animate-fade-up">
          <div className="min-w-0">
            <div className="text-xs font-mono text-muted-foreground uppercase tracking-widest mb-2">
              Repository
            </div>
            <h1 className="text-3xl font-semibold tracking-tight">{repo.name}</h1>
            <p className="text-muted-foreground mt-3 max-w-2xl text-pretty">{repo.description}</p>
            <div className="flex flex-wrap gap-1.5 mt-4">
              {repo.tags.map((t) => (
                <span
                  key={t}
                  className="text-[10px] font-mono px-2 py-0.5 rounded bg-secondary text-zinc-300"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
          <div className="flex flex-wrap gap-2 shrink-0">
            <a className="bg-foreground text-background text-sm font-medium py-2 px-4 rounded-md hover:bg-foreground/90 transition-colors inline-flex items-center gap-1.5">
              Open on GitHub <ExternalLink className="size-3.5" />
            </a>
            <button className="bg-secondary border border-border text-sm py-2 px-3 rounded-md hover:bg-secondary/70 inline-flex items-center gap-1.5">
              <GitCompare className="size-3.5" /> Compare
            </button>
            <button className="bg-secondary border border-border text-sm py-2 px-3 rounded-md hover:bg-secondary/70 inline-flex items-center gap-1.5">
              <Bookmark className="size-3.5" /> Save
            </button>
          </div>
        </header>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 animate-fade-up">
          {stats.map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.label} className="bg-surface ring-1 ring-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Icon className="size-3.5" />
                  <span className="text-[10px] font-mono uppercase tracking-widest">{s.label}</span>
                </div>
                <div className="text-2xl font-semibold mt-2">{s.value}</div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card title="README summary" icon={BookOpen} className="lg:col-span-2">
            <p className="text-sm text-zinc-300 leading-relaxed">
              {repo.description} The project ships with a modular core, an opinionated CLI, and first-class
              TypeScript support. Adoption is strong across mid-size SaaS teams, and the maintainers ship
              breaking changes through a deliberate RFC process.
            </p>
            <ul className="mt-4 space-y-2 text-sm text-zinc-300 list-disc list-inside marker:text-accent">
              <li>Modern, dependency-light core</li>
              <li>Comprehensive examples and starter templates</li>
              <li>Active Discord and weekly release cadence</li>
            </ul>
          </Card>

          <Card title="Architecture" icon={Layers}>
            <ul className="space-y-3 text-sm">
              <Row k="Pattern" v="Plugin-driven" />
              <Row k="Runtime" v="Node + Edge" />
              <Row k="State" v="Stateless workers" />
              <Row k="Storage" v="Pluggable adapters" />
            </ul>
          </Card>

          <Card title="Tech stack analysis" icon={Gauge} className="lg:col-span-2">
            <div className="space-y-3">
              {repo.tags.map((t, i) => (
                <div key={t}>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-zinc-300 font-medium">{t}</span>
                    <span className="text-muted-foreground font-mono">{90 - i * 12}%</span>
                  </div>
                  <div className="h-1.5 bg-canvas/60 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent/80 rounded-full"
                      style={{ width: `${90 - i * 12}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Contributor activity" icon={Users}>
            <div className="flex items-end gap-1.5 h-24">
              {[40, 60, 35, 75, 55, 90, 70, 80, 50, 95, 65, 78].map((h, i) => (
                <div
                  key={i}
                  className="flex-1 bg-accent/70 hover:bg-accent rounded-sm transition-colors"
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
            <div className="flex justify-between text-[10px] font-mono text-muted-foreground mt-2 uppercase tracking-widest">
              <span>12 wks ago</span>
              <span>Today</span>
            </div>
          </Card>

          <Card title="Repo health" icon={Activity} className="lg:col-span-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { k: "Issue close rate", v: "92%" },
                { k: "PR merge time", v: "1.8d" },
                { k: "Test coverage", v: "87%" },
                { k: "Security advisories", v: "0 open" },
              ].map((m) => (
                <div key={m.k}>
                  <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                    {m.k}
                  </div>
                  <div className="text-xl font-semibold mt-1">{m.v}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <section>
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-widest mb-5">
            Similar repositories
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {similar.map((r) => (
              <RepoCard key={r.slug} repo={r} />
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Card({
  title,
  icon: Icon,
  children,
  className = "",
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-surface ring-1 ring-white/5 rounded-xl p-5 ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <Icon className="size-3.5 text-accent" />
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <li className="flex justify-between items-center">
      <span className="text-xs text-muted-foreground font-mono uppercase tracking-wider">{k}</span>
      <span className="text-sm text-zinc-200">{v}</span>
    </li>
  );
}
