import { Link, useRouterState } from "@tanstack/react-router";
import {
  Home,
  Compass,
  GitCompare,
  FolderHeart,
  Bookmark,
  History,
  TrendingUp,
  Settings,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

const mainNav = [
  { to: "/", label: "Home", icon: Home },
  { to: "/discover", label: "Discover", icon: Compass },
  { to: "/compare", label: "Compare", icon: GitCompare },
  { to: "/collections", label: "Collections", icon: FolderHeart },
];

const libraryNav = [
  { to: "/saved", label: "Saved Repos", icon: Bookmark },
  { to: "/history", label: "Search History", icon: History },
  { to: "/trending", label: "Trending", icon: TrendingUp },
];

export function AppSidebar({
  isMobile = false,
  forceExpanded = false,
  onClose,
}: {
  isMobile?: boolean;
  forceExpanded?: boolean;
  onClose?: () => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = useRouterState({ select: (r) => r.location.pathname });

  // Auto-collapse on tablet viewport sizes
  useEffect(() => {
    if (isMobile) return;
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setCollapsed(true);
      } else {
        setCollapsed(false);
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [isMobile]);

  const isCollapsed = collapsed && !forceExpanded;

  return (
    <aside
      className={cn(
        "border-r border-sidebar-border bg-sidebar flex flex-col shrink-0 h-screen transition-[width] duration-200 z-30",
        isMobile ? "w-full h-full" : "sticky top-0",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className="p-4 flex items-center justify-between">
        <Link 
          to="/" 
          onClick={onClose}
          className="flex items-center gap-3 overflow-hidden"
        >
          <div className="size-7 rounded-md bg-accent/15 ring-1 ring-accent/40 flex items-center justify-center shrink-0">
            <div className="size-2 bg-accent rounded-full" />
          </div>
          {!isCollapsed && (
            <span className="font-semibold tracking-tight text-sm">GitSuggest</span>
          )}
        </Link>
        {!isMobile && (
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="text-muted-foreground hover:text-foreground p-1.5 rounded-md hover:bg-secondary/60 transition-colors"
            aria-label="Toggle sidebar"
          >
            {isCollapsed ? <PanelLeft className="size-4" /> : <PanelLeftClose className="size-4" />}
          </button>
        )}
      </div>

      <nav className="flex-1 px-3 space-y-0.5 mt-2">
        {mainNav.map((item) => (
          <NavItem 
            key={item.to} 
            {...item} 
            active={pathname === item.to} 
            collapsed={isCollapsed} 
            onClick={onClose}
          />
        ))}

        {!isCollapsed && (
          <div className="mt-8 px-3 py-2 text-[10px] font-semibold text-muted-foreground/70 uppercase tracking-widest">
            Library
          </div>
        )}
        {isCollapsed && <div className="my-4 mx-3 h-px bg-sidebar-border" />}

        {libraryNav.map((item) => (
          <NavItem 
            key={item.to} 
            {...item} 
            active={pathname === item.to} 
            collapsed={isCollapsed} 
            onClick={onClose}
          />
        ))}
      </nav>

      <div className="p-3 border-t border-sidebar-border space-y-1">
        <NavItem 
          to="/settings" 
          label="Settings" 
          icon={Settings} 
          active={pathname === "/settings"} 
          collapsed={isCollapsed} 
          onClick={onClose}
        />
        <button className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-secondary/60 transition-colors text-left">
          <div className="size-8 rounded-full bg-gradient-to-br from-accent/60 to-accent/20 ring-1 ring-white/10 shrink-0 grid place-items-center text-[10px] font-mono font-semibold text-accent-foreground">
            AD
          </div>
          {!isCollapsed && (
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium truncate">alex_dev</div>
              <div className="text-[10px] text-muted-foreground truncate">Pro Plan</div>
            </div>
          )}
        </button>
      </div>
    </aside>
  );
}

function NavItem({
  to,
  label,
  icon: Icon,
  active,
  collapsed,
  onClick,
}: {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  active: boolean;
  collapsed: boolean;
  onClick?: () => void;
}) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className={cn(
        "group flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
        active
          ? "bg-secondary/70 text-foreground"
          : "text-muted-foreground hover:text-foreground hover:bg-secondary/40"
      )}
    >
      <Icon className="size-4 shrink-0" />
      {!collapsed && <span className="text-sm font-medium truncate">{label}</span>}
    </Link>
  );
}
