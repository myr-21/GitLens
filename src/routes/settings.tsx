import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
  head: () => ({ meta: [{ title: "Settings — GitSuggest" }] }),
});

const sections = [
  {
    title: "Account",
    fields: [
      { label: "Display name", value: "alex_dev" },
      { label: "Email", value: "alex@gitsuggest.dev" },
    ],
  },
  {
    title: "Preferences",
    fields: [
      { label: "Default language", value: "TypeScript" },
      { label: "Difficulty bias", value: "Intermediate" },
    ],
  },
];

function SettingsPage() {
  return (
    <AppShell>
      <div className="max-w-3xl mx-auto w-full px-8 py-12 space-y-10">
        <header className="animate-fade-up">
          <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-2">Tune the engine to your workflow.</p>
        </header>

        {sections.map((s) => (
          <section key={s.title} className="bg-surface ring-1 ring-white/5 rounded-2xl p-6 space-y-5">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              {s.title}
            </h2>
            <div className="space-y-4">
              {s.fields.map((f) => (
                <div key={f.label} className="grid grid-cols-1 md:grid-cols-[160px_1fr] gap-3 items-center">
                  <label className="text-sm text-zinc-300">{f.label}</label>
                  <input
                    defaultValue={f.value}
                    className="bg-canvas/60 border border-border rounded-md px-3 py-2 text-sm outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/40"
                  />
                </div>
              ))}
            </div>
          </section>
        ))}

        <div className="flex justify-end">
          <button className="bg-foreground text-background text-sm font-medium px-4 py-2 rounded-md hover:bg-foreground/90">
            Save changes
          </button>
        </div>
      </div>
    </AppShell>
  );
}
