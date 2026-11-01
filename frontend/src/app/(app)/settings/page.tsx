"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Check } from "lucide-react";
import { useUser } from "@/components/app-shell";
import { applyTheme } from "@/components/theme";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FormError, Input, Label, Select } from "@/components/ui/form";
import { api, ApiError } from "@/lib/api";
import { CEFR_LEVELS, type Preferences } from "@/lib/types";

export default function SettingsPage() {
  const { user, setUser } = useUser();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const p = user.preferences;

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const patch: Partial<Preferences> = {
      explanation_language: String(f.get("explanation_language")),
      show_hindi: f.get("show_hindi") === "on",
      cefr_level: String(f.get("cefr_level")) as Preferences["cefr_level"],
      daily_new_cards: Number(f.get("daily_new_cards")),
      daily_review_limit: Number(f.get("daily_review_limit")),
      timezone: String(f.get("timezone")),
      theme: String(f.get("theme")) as Preferences["theme"],
    };
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const prefs = await api.updatePreferences(patch);
      setUser({ ...user, preferences: prefs });
      applyTheme(prefs.theme);
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save settings.");
    } finally {
      setSaving(false);
    }
  }

  async function deleteAccount() {
    const typed = prompt(`This permanently deletes your account and all your vocabulary.\nType your email (${user.email}) to confirm.`);
    if (typed?.trim().toLowerCase() !== user.email) return;
    setDeleting(true);
    try {
      await api.deleteAccount();
      router.replace("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't delete your account.");
      setDeleting(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="font-display text-3xl">Settings</h1>
      <form onSubmit={onSubmit} onChange={() => setSaved(false)}>
        <Card className="space-y-5">
          <h2 className="font-medium">Learning</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="target">Learning</Label>
              <Input id="target" value="German" disabled />
            </div>
            <div>
              <Label htmlFor="explanation_language">Explanations in</Label>
              <Select id="explanation_language" name="explanation_language" defaultValue={p.explanation_language}>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="cefr_level">Your level</Label>
              <Select id="cefr_level" name="cefr_level" defaultValue={p.cefr_level}>
                {CEFR_LEVELS.map((l) => <option key={l}>{l}</option>)}
              </Select>
            </div>
            <label className="flex items-center gap-2 self-end pb-2 text-sm">
              <input type="checkbox" name="show_hindi" defaultChecked={p.show_hindi} className="h-4 w-4 accent-[rgb(var(--accent))]" />
              Also show Hindi translations
            </label>
            <div>
              <Label htmlFor="daily_new_cards">New words per day</Label>
              <Input id="daily_new_cards" name="daily_new_cards" type="number" min={0} max={500} defaultValue={p.daily_new_cards} required />
            </div>
            <div>
              <Label htmlFor="daily_review_limit">Max reviews per day</Label>
              <Input id="daily_review_limit" name="daily_review_limit" type="number" min={0} max={2000} defaultValue={p.daily_review_limit} required />
            </div>
          </div>

          <h2 className="pt-2 font-medium">Display</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="theme">Theme</Label>
              <Select id="theme" name="theme" defaultValue={p.theme}>
                <option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="timezone">Time zone</Label>
              <Input id="timezone" name="timezone" defaultValue={p.timezone} required maxLength={64} />
            </div>
          </div>
          <FormError message={error} />
          <div className="flex items-center gap-3">
            <Button type="submit" loading={saving}>Save settings</Button>
            {saved && <span className="flex items-center gap-1 text-sm text-good"><Check className="h-4 w-4" /> Saved</span>}
          </div>
        </Card>
      </form>

      <Card className="border-bad/30">
        <h2 className="font-medium text-bad">Delete account</h2>
        <p className="mt-1 text-sm text-muted">Removes your account, vocabulary, uploads and learning history permanently.</p>
        <Button variant="danger" className="mt-4" onClick={deleteAccount} loading={deleting}>Delete my account</Button>
      </Card>
    </div>
  );
}
