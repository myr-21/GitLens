import { AppSidebar } from "./AppSidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full bg-canvas text-foreground selection:bg-accent/30">
      <AppSidebar />
      <main className="flex-1 flex flex-col min-w-0">{children}</main>
    </div>
  );
}
