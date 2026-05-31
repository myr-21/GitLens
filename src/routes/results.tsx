import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { AppShell } from "@/components/AppShell";
import { RepoCard } from "@/components/RepoCard";
import { fetchSuggestions, type SuggestResponse } from "@/lib/api";
import {
  Search,
  SlidersHorizontal,
  Loader2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { useState, useEffect, useRef } from "react";

const searchSchema = z.object({
  q: fallback(z.string(), "").default(""),
  lang: fallback(z.string(), "").default(""),
  limit: fallback(z.number(), 10).default(10),
});

export const Route = createFileRoute("/results")({
  validateSearch: zodValidator(searchSchema),
  component: Results,
  head: () => ({ meta: [{ title: "Results — GitSuggest" }] }),
});

const LANGUAGES = ["Any", "Python", "TypeScript", "JavaScript", "Go", "Rust", "Java", "C++"];

function Results() {
  const { q, lang, limit } = Route.useSearch();
  const navigate = useNavigate();
  const [query, setQuery] = useState(q);
  const [language, setLanguage] = useState(lang);

  const [data, setData] = useState<SuggestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Abort controller so in-flight requests are cancelled when a new one starts
  const abortRef = useRef<AbortController | null>(null);

  const runSearch = async (description: string, lang: string) => {
    if (!description.trim()) return;

    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const result = await fetchSuggestions({
        description,
        language: lang && lang !== "Any" ? lang : null,
        limit,
      });
      setData(result);
    } catch (err: any) {
      if (err.name === "AbortError") return;
      setError(err.message ?? "Something went wrong. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  // Run on mount and whenever the URL search params change
  useEffect(() => {
    if (q) runSearch(q, lang);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, lang, limit]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate({ to: "/results", search: { q: query, lang: language, limit } });
  };

  return (
    <AppShell>
      {/* Sticky search bar */}
      <div className="sticky top-0 z-20 bg-canvas/85 backdrop-blur-md border-b border-border">
        <div className="max-w-6xl mx-auto px-8 py-4 flex items-center gap-3">
          <form onSubmit={handleSubmit} className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-4 text-muted-foreground/60" />
            <input
              type="text"
              id="results-search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search projects, tech stacks, or ideas…"
              className="w-full bg-surface border border-border rounded-lg py-2.5 pl-11 pr-4 text-sm outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/40 transition-all"
            />
          </form>

          {/* Language filter */}
          <select
            id="language-filter"
            value={language}
            onChange={(e) => {
              setLanguage(e.target.value);
              navigate({
                to: "/results",
                search: { q: query, lang: e.target.value, limit },
              });
            }}
            className="bg-surface border border-border rounded-lg px-3 py-2.5 text-sm text-zinc-200 outline-none focus:border-accent/40 cursor-pointer"
          >
            {LANGUAGES.map((l) => (
              <option key={l} value={l === "Any" ? "" : l}>
                {l}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={handleSubmit}
            className="inline-flex items-center gap-2 px-3 py-2.5 rounded-lg bg-surface border border-border text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <SlidersHorizontal className="size-4" /> Search
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto w-full px-8 py-8">
        {/* Header */}
        <div className="mb-6 flex items-baseline justify-between">
          <div>
            <h1 className="text-xl font-semibold">
              {q ? (
                <>
                  Results for{" "}
                  <span className="font-mono text-accent">"{q}"</span>
                </>
              ) : (
                "All repositories"
              )}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {loading
                ? "Searching…"
                : data
                ? `${data.suggestions.length} suggestions · ranked by intelligent match`
                : "Enter a description above to find matching repositories."}
            </p>
          </div>
        </div>

        {/* Intent summary banner */}
        {data?.intent_summary && (
          <div className="mb-6 flex items-start gap-3 bg-accent/5 border border-accent/20 rounded-xl px-5 py-3">
            <Sparkles className="size-4 text-accent mt-0.5 shrink-0" />
            <div>
              <p className="text-sm text-zinc-300">{data.intent_summary}</p>
              {data.follow_up_question && (
                <p className="text-xs text-muted-foreground mt-1 italic">
                  💬 {data.follow_up_question}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-32 gap-4 text-muted-foreground">
            <Loader2 className="size-8 animate-spin text-accent" />
            <p className="text-sm">Analysing your description with BERT embeddings…</p>
          </div>
        )}

        {/* Error state */}
        {!loading && error && (
          <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/20 rounded-xl px-5 py-4 text-red-400">
            <AlertCircle className="size-5 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium">Backend error</p>
              <p className="text-xs mt-0.5 opacity-80">{error}</p>
              <p className="text-xs mt-1 opacity-60">
                Make sure the FastAPI server is running on{" "}
                <code className="font-mono">http://localhost:8000</code>
              </p>
            </div>
          </div>
        )}

        {/* Results grid */}
        {!loading && data && data.suggestions.length > 0 && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {data.suggestions.map((s) => (
              <RepoCard key={s.repo} suggestion={s} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && data && data.suggestions.length === 0 && (
          <div className="text-center py-24 text-muted-foreground">
            <p className="text-lg font-medium">No repositories found</p>
            <p className="text-sm mt-1">Try rephrasing your description or removing filters.</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
