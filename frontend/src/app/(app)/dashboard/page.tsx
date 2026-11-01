"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, BookMarked, CalendarCheck, Flame, Plus, RefreshCw, Sparkles, Trophy } from "lucide-react";
import { useUser } from "@/components/app-shell";
import { buttonVariants, Button } from "@/components/ui/button";
import { Card, Skeleton } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";
import { CEFR_LEVELS, type Dashboard } from "@/lib/types";

function greeting() {
  const h = new Date().getHours();
  return h < 11 ? "Guten Morgen" : h < 18 ? "Guten Tag" : "Guten Abend";
}

function Stat({ icon: Icon, label, value, sub }: { icon: typeof Flame; label: string; value: React.ReactNode; sub?: string }) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 text-xs text-muted"><Icon className="h-3.5 w-3.5" />{label}</div>
      <p className="mt-2 font-display text-3xl tabular-nums">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-muted">{sub}</p>}
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useUser();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api.dashboard().then(setData).catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load your dashboard."));
  };
  useEffect(load, []);

  if (error) {
    return (
      <Card className="flex flex-col items-start gap-3">
        <p className="text-bad">{error}</p>
        <Button variant="secondary" size="sm" onClick={load}><RefreshCw className="h-4 w-4" /> Try again</Button>
      </Card>
    );
  }

  const goal = data?.daily_new_goal ?? 0;
  const goalPct = data && goal ? Math.min(100, Math.round((data.new_today / goal) * 100)) : 0;
  const maxDay = data ? Math.max(1, ...data.last_7_days.map((d) => d.cards_added + d.reviews)) : 1;
  const totalCefr = data ? Object.values(data.cefr_distribution).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl">{greeting()}, {user.display_name}</h1>
          <p className="mt-1 text-sm text-muted">Level {user.preferences.cefr_level} · German</p>
        </div>
        <Link href="/vocabulary?new=1" className={buttonVariants()}><Plus className="h-4 w-4" /> Add word</Link>
      </div>

      {!data ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
      ) : (
        <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat icon={BookMarked} label="Total words" value={data.total_cards} sub={`${data.new_today} added today`} />
            <Stat icon={CalendarCheck} label="Due for review" value={data.due_now} sub={`${data.reviews_today} reviewed today`} />
            <Stat icon={Trophy} label="Mastered" value={data.mastered} />
            <Stat icon={Flame} label="Streak" value={`${data.streak_days} ${data.streak_days === 1 ? "day" : "days"}`} />
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <Card>
              <div className="flex items-center justify-between">
                <h2 className="font-medium">Last 7 days</h2>
                <div className="flex gap-3 text-xs text-muted">
                  <span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-accent" />Added</span>
                  <span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-good" />Reviewed</span>
                </div>
              </div>
              <div className="mt-6 flex items-end gap-2" role="img"
                   aria-label={data.last_7_days.map((d) => `${d.day}: ${d.cards_added} added, ${d.reviews} reviewed`).join("; ")}>
                {data.last_7_days.map((d) => {
                  const total = d.cards_added + d.reviews;
                  return (
                    <div key={d.day} className="flex flex-1 flex-col items-center gap-2">
                      <div className="flex h-32 w-full max-w-[36px] flex-col justify-end overflow-hidden rounded-lg bg-line/40"
                           title={`${d.cards_added} added · ${d.reviews} reviewed`}>
                        <div className="w-full bg-good" style={{ height: `${(d.reviews / maxDay) * 100}%` }} />
                        <div className="w-full bg-accent" style={{ height: `${(d.cards_added / maxDay) * 100}%` }} />
                      </div>
                      <span className="text-[11px] text-muted">
                        {new Date(d.day + "T12:00:00").toLocaleDateString("de-DE", { weekday: "short" })}
                      </span>
                      <span className="sr-only">{total}</span>
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card className="space-y-5">
              <div>
                <div className="flex items-baseline justify-between">
                  <h2 className="font-medium">Today&apos;s goal</h2>
                  <span className="text-sm tabular-nums text-muted">{data.new_today} / {goal} new words</span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-line/60">
                  <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${goalPct}%` }} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted">Retention (30 days)</p>
                  <p className="mt-1 font-display text-2xl">
                    {data.retention_30d === null ? <span className="text-base text-muted">No reviews yet</span>
                      : `${Math.round(data.retention_30d * 100)}%`}
                  </p>
                </div>
                <div>
                  <p className="flex items-center gap-1 text-xs text-muted"><AlertTriangle className="h-3 w-3" />Difficult</p>
                  <p className="mt-1 font-display text-2xl">{data.difficult}</p>
                </div>
              </div>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="font-medium">CEFR distribution</h2>
              {totalCefr === 0 ? (
                <p className="mt-3 text-sm text-muted">Levels appear here once you add words with a CEFR level.</p>
              ) : (
                <div className="mt-4 space-y-2">
                  {[...CEFR_LEVELS, "unknown"].map((lvl) => {
                    const n = data.cefr_distribution[lvl] ?? 0;
                    if (lvl === "unknown" && n === 0) return null;
                    return (
                      <div key={lvl} className="flex items-center gap-3 text-sm">
                        <span className="w-14 text-muted">{lvl === "unknown" ? "Not set" : lvl}</span>
                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-line/50">
                          <div className="h-full rounded-full bg-accent/80" style={{ width: `${(n / totalCefr) * 100}%` }} />
                        </div>
                        <span className="w-8 text-right tabular-nums">{n}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
            <Card>
              <h2 className="flex items-center gap-2 font-medium"><Sparkles className="h-4 w-4 text-accent" /> Next steps</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {data.recommendations.map((r) => <li key={r} className="rounded-xl bg-bg px-3 py-2">{r}</li>)}
              </ul>
            </Card>
          </div>
        </motion.div>
      )}
    </div>
  );
}
