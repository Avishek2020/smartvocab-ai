"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormError, Input, Label, Select, Textarea } from "@/components/ui/form";
import { api, ApiError } from "@/lib/api";
import { CEFR_LEVELS, PARTS_OF_SPEECH, type Card, type Collection, type PartOfSpeech } from "@/lib/types";

const splitList = (s: string) => s.split(/[\n,;]/).map((x) => x.trim()).filter(Boolean);
const g = (card: Card | null, key: string) => (card?.grammar?.[key] as string | undefined) ?? "";

type Props = {
  card: Card | null;
  collections: Collection[];
  showHindi: boolean;
  onClose: () => void;
  onSaved: (card: Card) => void;
};

export function CardEditor({ card, collections, showHindi, onClose, onSaved }: Props) {
  const [pos, setPos] = useState<PartOfSpeech>(card?.part_of_speech ?? "noun");
  const [separable, setSeparable] = useState<boolean>(Boolean(card?.grammar?.separable));
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const prep = (card?.grammar?.prepositions as { preposition: string; case: string }[] | undefined)?.[0];

  function buildGrammar(f: FormData): Record<string, unknown> | null {
    const v = (k: string) => String(f.get(k) ?? "").trim() || undefined;
    let out: Record<string, unknown> = {};
    if (pos === "noun") {
      out = { article: v("article"), plural: v("plural"), genitive: v("genitive") };
      if (!out.article) return null;
    } else if (pos === "verb") {
      const p = v("prep");
      out = {
        infinitive: v("lemma") || v("term"),
        praeteritum: v("praeteritum"), partizip_ii: v("partizip_ii"), auxiliary: v("auxiliary"),
        separable: separable || undefined,
        separable_prefix: separable ? v("separable_prefix") : undefined,
        reflexive: v("reflexive"), object_case: v("object_case"),
        prepositions: p ? [{ preposition: p, case: v("prep_case") || "akkusativ" }] : undefined,
      };
    } else if (pos === "adjective") {
      out = { comparative: v("comparative"), superlative: v("superlative") };
    } else {
      return null;
    }
    const cleaned = Object.fromEntries(Object.entries(out).filter(([, x]) => x !== undefined));
    const meaningful = Object.keys(cleaned).filter((k) => k !== "infinitive");
    return meaningful.length ? cleaned : null;
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const s = (k: string) => String(f.get(k) ?? "").trim();
    const translations: Record<string, string> = {};
    if (s("tr_en")) translations.en = s("tr_en");
    if (s("tr_hi")) translations.hi = s("tr_hi");
    const examples = s("examples").split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
      const [sentence, translation] = line.split("|").map((x) => x.trim());
      return { sentence, translation: translation || null };
    });
    const payload = {
      term: s("term"),
      lemma: s("lemma") || null,
      sense_key: s("sense_key"),
      part_of_speech: pos,
      cefr_level: s("cefr_level") || null,
      translations,
      explanation: s("explanation") || null,
      source_sentence: s("source_sentence") || null,
      collocations: splitList(s("collocations")),
      synonyms: splitList(s("synonyms")),
      antonyms: splitList(s("antonyms")),
      personal_note: s("personal_note") || null,
      examples,
      grammar: buildGrammar(f),
      collection_ids: f.getAll("collection_ids").map(String),
      ...(card ? { status: card.status } : {}),
    };
    setSaving(true);
    setError(null);
    try {
      const saved = card ? await api.updateCard(card.id, payload) : await api.createCard(payload);
      onSaved(saved);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save the card.");
      setSaving(false);
    }
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  // Portal to <body> so the overlay is never clipped by a containing block in the layout.
  return createPortal(
    <div className="fixed inset-0 z-50 flex justify-end bg-ink/30 backdrop-blur-[2px]" onClick={onClose} role="dialog" aria-modal="true">
      <form
        onSubmit={onSubmit}
        onClick={(e) => e.stopPropagation()}
        className="flex h-full w-full max-w-xl flex-col bg-bg shadow-2xl"
        aria-label={card ? "Edit card" : "New card"}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="font-display text-xl">{card ? `Edit “${card.term}”` : "Add a word"}</h2>
          <Button type="button" variant="ghost" size="icon" onClick={onClose} aria-label="Close"><X className="h-4 w-4" /></Button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2 sm:col-span-1">
              <Label htmlFor="term">German word or phrase</Label>
              <Input id="term" name="term" required maxLength={200} defaultValue={card?.term} autoFocus lang="de" />
            </div>
            <div className="col-span-2 sm:col-span-1">
              <Label htmlFor="lemma" hint="(dictionary form)">Lemma</Label>
              <Input id="lemma" name="lemma" maxLength={200} defaultValue={card?.lemma !== card?.term ? card?.lemma : ""} lang="de" />
            </div>
            <div>
              <Label htmlFor="pos">Part of speech</Label>
              <Select id="pos" value={pos} onChange={(e) => setPos(e.target.value as PartOfSpeech)}>
                {PARTS_OF_SPEECH.map((p) => <option key={p} value={p}>{p}</option>)}
              </Select>
            </div>
            <div>
              <Label htmlFor="cefr_level">CEFR level</Label>
              <Select id="cefr_level" name="cefr_level" defaultValue={card?.cefr_level ?? ""}>
                <option value="">Not set</option>
                {CEFR_LEVELS.map((l) => <option key={l}>{l}</option>)}
              </Select>
            </div>
            <div>
              <Label htmlFor="tr_en">English</Label>
              <Input id="tr_en" name="tr_en" defaultValue={card?.translations.en} />
            </div>
            <div>
              <Label htmlFor="tr_hi" hint={showHindi ? undefined : "(optional)"}>Hindi</Label>
              <Input id="tr_hi" name="tr_hi" defaultValue={card?.translations.hi} lang="hi" />
            </div>
            <div className="col-span-2">
              <Label htmlFor="sense_key" hint="(only needed for a second meaning of the same word)">Sense</Label>
              <Input id="sense_key" name="sense_key" maxLength={120} placeholder="e.g. bench / financial" defaultValue={card?.sense_key} />
            </div>
          </div>

          {pos === "noun" && (
            <fieldset className="grid grid-cols-3 gap-3 rounded-2xl border border-line p-4">
              <legend className="px-1 text-sm font-medium">Noun</legend>
              <div>
                <Label htmlFor="article">Article</Label>
                <Select id="article" name="article" defaultValue={g(card, "article")}>
                  <option value="">—</option><option>der</option><option>die</option><option>das</option>
                </Select>
              </div>
              <div><Label htmlFor="plural">Plural</Label><Input id="plural" name="plural" defaultValue={g(card, "plural")} placeholder="die Termine" lang="de" /></div>
              <div><Label htmlFor="genitive">Genitive</Label><Input id="genitive" name="genitive" defaultValue={g(card, "genitive")} placeholder="des Termins" lang="de" /></div>
            </fieldset>
          )}

          {pos === "verb" && (
            <fieldset className="grid grid-cols-2 gap-3 rounded-2xl border border-line p-4">
              <legend className="px-1 text-sm font-medium">Verb</legend>
              <div><Label htmlFor="praeteritum">Präteritum</Label><Input id="praeteritum" name="praeteritum" defaultValue={g(card, "praeteritum")} lang="de" /></div>
              <div><Label htmlFor="partizip_ii">Partizip II</Label><Input id="partizip_ii" name="partizip_ii" defaultValue={g(card, "partizip_ii")} lang="de" /></div>
              <div>
                <Label htmlFor="auxiliary">Auxiliary</Label>
                <Select id="auxiliary" name="auxiliary" defaultValue={g(card, "auxiliary")}>
                  <option value="">—</option><option>haben</option><option>sein</option><option>haben/sein</option>
                </Select>
              </div>
              <div>
                <Label htmlFor="object_case">Object case</Label>
                <Select id="object_case" name="object_case" defaultValue={g(card, "object_case")}>
                  <option value="">—</option><option value="akkusativ">Akkusativ</option><option value="dativ">Dativ</option><option value="genitiv">Genitiv</option>
                </Select>
              </div>
              <div>
                <Label htmlFor="reflexive">Reflexive</Label>
                <Select id="reflexive" name="reflexive" defaultValue={g(card, "reflexive")}>
                  <option value="">—</option><option value="no">No</option><option value="akkusativ">sich (Akk.)</option>
                  <option value="dativ">sich (Dat.)</option><option value="optional">Optional</option>
                </Select>
              </div>
              <div className="flex items-end gap-2">
                <label className="flex h-10 items-center gap-2 text-sm">
                  <input type="checkbox" checked={separable} onChange={(e) => setSeparable(e.target.checked)} className="h-4 w-4 accent-[rgb(var(--accent))]" />
                  Separable
                </label>
                {separable && <Input name="separable_prefix" aria-label="Separable prefix" placeholder="teil" defaultValue={g(card, "separable_prefix")} />}
              </div>
              <div><Label htmlFor="prep">Preposition</Label><Input id="prep" name="prep" defaultValue={prep?.preposition} placeholder="an" lang="de" /></div>
              <div>
                <Label htmlFor="prep_case">+ case</Label>
                <Select id="prep_case" name="prep_case" defaultValue={prep?.case ?? "akkusativ"}>
                  <option value="akkusativ">Akkusativ</option><option value="dativ">Dativ</option><option value="genitiv">Genitiv</option>
                </Select>
              </div>
            </fieldset>
          )}

          {pos === "adjective" && (
            <fieldset className="grid grid-cols-2 gap-3 rounded-2xl border border-line p-4">
              <legend className="px-1 text-sm font-medium">Adjective</legend>
              <div><Label htmlFor="comparative">Comparative</Label><Input id="comparative" name="comparative" defaultValue={g(card, "comparative")} lang="de" /></div>
              <div><Label htmlFor="superlative">Superlative</Label><Input id="superlative" name="superlative" defaultValue={g(card, "superlative")} placeholder="am schnellsten" lang="de" /></div>
            </fieldset>
          )}

          <div>
            <Label htmlFor="source_sentence">Where you found it</Label>
            <Textarea id="source_sentence" name="source_sentence" defaultValue={card?.source_sentence ?? ""} lang="de" rows={2} />
          </div>
          <div>
            <Label htmlFor="examples" hint="(one per line: German | translation)">Examples</Label>
            <Textarea id="examples" name="examples" rows={3} lang="de"
              defaultValue={card?.examples.map((e) => (e.translation ? `${e.sentence} | ${e.translation}` : e.sentence)).join("\n")} />
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div><Label htmlFor="collocations">Collocations</Label><Textarea id="collocations" name="collocations" rows={2} defaultValue={card?.collocations.join("\n")} lang="de" /></div>
            <div><Label htmlFor="synonyms">Synonyms</Label><Textarea id="synonyms" name="synonyms" rows={2} defaultValue={card?.synonyms.join("\n")} lang="de" /></div>
            <div><Label htmlFor="antonyms">Antonyms</Label><Textarea id="antonyms" name="antonyms" rows={2} defaultValue={card?.antonyms.join("\n")} lang="de" /></div>
          </div>
          <div>
            <Label htmlFor="explanation">Explanation</Label>
            <Textarea id="explanation" name="explanation" rows={2} defaultValue={card?.explanation ?? ""} />
          </div>
          <div>
            <Label htmlFor="personal_note">Personal note</Label>
            <Textarea id="personal_note" name="personal_note" rows={2} defaultValue={card?.personal_note ?? ""} />
          </div>
          <fieldset>
            <legend className="mb-2 text-sm font-medium">Collections</legend>
            <div className="flex flex-wrap gap-2">
              {collections.map((c) => (
                <label key={c.id} className="flex cursor-pointer items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-sm has-[:checked]:border-accent has-[:checked]:bg-accent/10">
                  <input type="checkbox" name="collection_ids" value={c.id} defaultChecked={card?.collection_ids.includes(c.id)} className="sr-only" />
                  {c.name}
                </label>
              ))}
            </div>
          </fieldset>
        </div>

        <div className="space-y-3 border-t border-line px-5 py-4">
          <FormError message={error} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={saving}>{card ? "Save changes" : "Add card"}</Button>
          </div>
        </div>
      </form>
    </div>,
    document.body,
  );
}
