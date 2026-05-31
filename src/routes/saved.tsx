import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { RepoCard } from "@/components/RepoCard";
import { repos } from "@/lib/repos";

export const Route = createFileRoute("/saved")({
  component: Saved,
  head: () => ({ meta: [{ title: "Saved — GitSuggest" }] }),
});

function Saved() {
  return (
    <AppShell>
      <div className="max-w-6xl mx-auto w-full px-8 py-12">
        <header className="mb-8 animate-fade-up">
          <h1 className="text-3xl font-semibold tracking-tight">Saved repositories</h1>
          <p className="text-muted-foreground mt-2">Your bookmarked projects, ready to revisit.</p>
        </header>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {repos.slice(0, 4).map((r) => (
            <RepoCard key={r.slug} repo={r} />
          ))}
        </div>
      </div>
    </AppShell>
  );
}
