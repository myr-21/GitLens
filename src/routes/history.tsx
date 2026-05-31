import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { Search, Clock } from "lucide-react";

export const Route = createFileRoute("/history")({
  component: HistoryPage,
  head: () => ({ meta: [{ title: "Search history — GitSuggest" }] }),
});

const history = [
  { q: "MERN ecommerce", time: "2 min ago", count: 24 },
  { q: "Spring Boot JWT auth", time: "1 hour ago", count: 18 },
  { q: "Redis caching patterns", time: "Yesterday", count: 31 },
  { q: "Rust WASM image pipeline", time: "3 days ago", count: 9 },
  { q: "AI chatbot frameworks", time: "Last week", count: 47 },
];

function HistoryPage() {
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto w-full px-8 py-12">
        <header className="mb-8 animate-fade-up">
          <h1 className="text-3xl font-semibold tracking-tight">Search history</h1>
          <p className="text-muted-foreground mt-2">Recent queries and what you discovered.</p>
        </header>
        <div className="bg-surface ring-1 ring-white/5 rounded-2xl divide-y divide-border">
          {history.map((h) => (
            <Link
              key={h.q}
              to="/results"
              search={{ q: h.q }}
              className="flex items-center gap-4 px-5 py-4 hover:bg-secondary/40 first:rounded-t-2xl last:rounded-b-2xl transition-colors"
            >
              <Search className="size-4 text-muted-foreground shrink-0" />
              <span className="flex-1 text-sm font-medium truncate">{h.q}</span>
              <span className="text-xs text-muted-foreground font-mono">{h.count} results</span>
              <span className="text-xs text-muted-foreground inline-flex items-center gap-1 w-28 justify-end">
                <Clock className="size-3" /> {h.time}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
