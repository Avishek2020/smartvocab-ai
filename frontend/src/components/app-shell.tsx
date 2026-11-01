"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";
import { BookMarked, LayoutDashboard, LogOut, Settings } from "lucide-react";
import { ThemeToggle, applyTheme, type Theme } from "@/components/theme";
import { Skeleton } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { cn } from "@/lib/utils";

// Only pages that exist are listed. Later phases add their entries here.
const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/vocabulary", label: "Vocabulary", icon: BookMarked },
  { href: "/settings", label: "Settings", icon: Settings },
];

const UserContext = createContext<{ user: User; setUser: (u: User) => void } | null>(null);
export const useUser = () => {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used inside AppShell");
  return ctx;
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    api.me().then((u) => {
      setUser(u);
      applyTheme(u.preferences.theme);
    }).catch(() => {/* 401 handled in api client */});
  }, []);

  async function signOut() {
    setSigningOut(true);
    try {
      await api.logout();
    } finally {
      router.replace("/login");
      router.refresh();
    }
  }

  function saveTheme(t: Theme) {
    api.updatePreferences({ theme: t }).catch(() => {});
  }

  return (
    <div className="min-h-screen md:grid md:grid-cols-[220px_1fr]">
      <aside className="sticky top-0 z-20 flex items-center justify-between border-b border-line bg-bg/90 px-4 py-3 backdrop-blur md:h-screen md:flex-col md:items-stretch md:justify-start md:border-b-0 md:border-r md:px-3 md:py-5">
        <Link href="/dashboard" className="px-2 font-display text-lg font-semibold">
          SmartVocab<span className="text-accent"> AI</span>
        </Link>
        <nav className="flex gap-1 md:mt-8 md:flex-col" aria-label="Main">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2.5 rounded-xl px-2.5 py-2 text-sm transition-colors",
                  active ? "bg-surface font-medium text-ink shadow-sm ring-1 ring-line" : "text-muted hover:bg-line/40 hover:text-ink",
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-1 md:mt-auto md:flex-col md:items-stretch md:gap-2">
          <div className="hidden px-2.5 text-sm md:block">
            {user ? (
              <>
                <p className="truncate font-medium">{user.display_name}</p>
                <p className="truncate text-xs text-muted">{user.email}</p>
              </>
            ) : (
              <Skeleton className="h-9 w-full" />
            )}
          </div>
          <div className="flex items-center gap-1">
            <ThemeToggle onChange={saveTheme} />
            <button
              onClick={signOut}
              disabled={signingOut}
              className="inline-flex h-9 items-center gap-2 rounded-xl px-2.5 text-sm text-muted hover:bg-line/50 hover:text-ink disabled:opacity-50"
            >
              <LogOut className="h-4 w-4" /> <span className="hidden md:inline">Sign out</span>
            </button>
          </div>
        </div>
      </aside>
      <main className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
        {user ? (
          <UserContext.Provider value={{ user, setUser }}>{children}</UserContext.Provider>
        ) : (
          <div className="space-y-4"><Skeleton className="h-10 w-64" /><Skeleton className="h-32" /></div>
        )}
      </main>
    </div>
  );
}
