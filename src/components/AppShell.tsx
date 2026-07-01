import { useState, useEffect } from "react";
import { AppSidebar } from "./AppSidebar";
import { Menu, X } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close drawer on ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMobileOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Prevent background scrolling when drawer is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <div className="flex min-h-screen w-full bg-canvas text-foreground selection:bg-accent/30 relative">
      {/* Mobile/Tablet Top Bar (Visible under lg breakpoint) */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-sidebar border-b border-sidebar-border z-20 flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 text-muted-foreground hover:text-foreground rounded-md hover:bg-secondary/60 transition-colors focus:outline-none focus:ring-1 focus:ring-accent min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Open navigation menu"
          >
            <Menu className="size-5" />
          </button>
          <Link to="/" className="flex items-center gap-2">
            <div className="size-6 rounded bg-accent/15 ring-1 ring-accent/40 flex items-center justify-center">
              <div className="size-1.5 bg-accent rounded-full" />
            </div>
            <span className="font-semibold tracking-tight text-sm">GitSuggest</span>
          </Link>
        </div>
      </header>

      {/* Desktop/Tablet Sidebar (Hidden under sm breakpoint, visible on tablet collapsed or desktop expanded) */}
      <div className="hidden sm:block">
        <AppSidebar />
      </div>

      {/* Mobile Navigation Drawer Wrapper */}
      <div
        className={cn(
          "fixed inset-0 z-40 lg:hidden transition-opacity duration-200",
          mobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
      >
        {/* Outside Click Overlay */}
        <div
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />

        {/* Slide-out Sidebar Content Container */}
        <div
          className={cn(
            "absolute top-0 bottom-0 left-0 w-64 max-w-[80vw] bg-sidebar border-r border-sidebar-border transition-transform duration-200 transform",
            mobileOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <div className="absolute top-2 right-2 z-50">
            <button
              onClick={() => setMobileOpen(false)}
              className="p-2 text-muted-foreground hover:text-foreground rounded-md hover:bg-secondary/60 transition-colors focus:outline-none focus:ring-1 focus:ring-accent min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Close navigation menu"
            >
              <X className="size-5" />
            </button>
          </div>

          {/* Expanded Mobile Sidebar View */}
          <div className="h-full pt-10">
            <AppSidebar isMobile forceExpanded onClose={() => setMobileOpen(false)} />
          </div>
        </div>
      </div>

      {/* Main Page Layout Wrapper, pushed down on mobile by header height */}
      <main className="flex-1 flex flex-col min-w-0 pt-14 sm:pt-0">
        {children}
      </main>
    </div>
  );
}
