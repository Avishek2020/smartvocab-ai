"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useUser } from "@/components/app-shell";
import { CardEditor } from "@/components/card-editor";
import { Button } from "@/components/ui/button";
import { Badge, Card, Skeleton } from "@/components/ui/card";
import { FormError, Input, Select } from "@/components/ui/form";
import { api, ApiError } from "@/lib/api";
import { CEFR_LEVELS, PARTS_OF_SPEECH, type Card as VCard, type CardPage, type Collection } from "@/lib/types";

const PAGE_SIZE = 20;

function grammarSummary(c: VCard): string | null {
  const gr = c.grammar as Record<string, any> | null;
  if (!gr) return null;
  if (gr.pos === "noun") return [gr.article, gr.plural && `Pl. ${gr.plural}`].filter(Boolean).join(" · ");
  if (gr.pos === "verb")
    return [gr.auxiliary && gr.partizip_ii && `${gr.auxiliary === "sein" ? "ist" : "hat"} ${gr.partizip_ii}`,
            gr.prepositions?.[0] && `${gr.prepositions[0].preposition} + ${gr.prepositions[0].case}`,
            gr.separable && "trennbar"].filter(Boolean).join(" · ");
  if (gr.pos === "adjective") return [gr.comparative, gr.superlative].filter(Boolean).join(" · ");
  return null;
}

export default function VocabularyPage() {
  return (
    <Suspense>
      <VocabularyInner />
    </Suspense>
  );
}

function VocabularyInner() {
  const { user } = useUser();
  const router = useRouter();
  const params = useSearchParams();
  const [page, setPage] = useState<CardPage | null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [filters, setFilters] = useState({ q: "", cefr: "", pos: "", collection_id: "", page: 1 });
  const [editing, setEditing] = useState<VCard | null | "new">(params.get("new") ? "new" : null);
  const [error, setError] = useState<string | null>(null);
  const [debouncedQ, setDebouncedQ] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(filters.q), 250);
    return () => clearTimeout(t);
  }, [filters.q]);

  const load = useCallback(() => {
    setError(null);
    api.listCards({ ...filters, q: debouncedQ, page_size: PAGE_SIZE })
      .then(setPage)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load your vocabulary."));
  }, [filters.cefr, filters.pos, filters.collection_id, filters.page, debouncedQ]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(load, [load]);
  useEffect(() => { api.collections().then(setCollections).catch(() => {}); }, []);

  const set = (k: keyof typeof filters, v: string) => setFilters((f) => ({ ...f, [k]: v, page: 1 }));
  const closeEditor = () => {
    setEditing(null);
    if (params.get("new")) router.replace("/vocabulary");
  };

  async function remove(c: VCard) {
    if (!confirm(`Delete “${c.term}”? This can't be undone.`)) return;
    try {
      await api.deleteCard(c.id);
      load();
      api.collections().then(setCollections).catch(() => {});
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't delete the card.");
    }
  }

  const pages = page ? Math.max(1, Math.ceil(page.total / PAGE_SIZE)) : 1;
  const filtering = Boolean(debouncedQ || filters.cefr || filters.pos || filters.collection_id);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl">Vocabulary</h1>
          <p className="mt-1 text-sm text-muted">{page ? `${page.total} ${page.total === 1 ? "word" : "words"}` : " "}</p>
        </div>
        <Button onClick={() => setEditing("new")}><Plus className="h-4 w-4" /> Add word</Button>
      </div>

      <div className="grid gap-2 sm:grid-cols-[1fr_auto_auto_auto]">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <Input className="pl-9" placeholder="Search German or translation…" value={filters.q}
                 onChange={(e) => set("q", e.target.value)} aria-label="Search vocabulary" />
        </div>
        <Select aria-label="CEFR level" value={filters.cefr} onChange={(e) => set("cefr", e.target.value)}>
          <option value="">All levels</option>{CEFR_LEVELS.map((l) => <option key={l}>{l}</option>)}
        </Select>
        <Select aria-label="Part of speech" value={filters.pos} onChange={(e) => set("pos", e.target.value)}>
          <option value="">All types</option>{PARTS_OF_SPEECH.map((p) => <option key={p}>{p}</option>)}
        </Select>
        <Select aria-label="Collection" value={filters.collection_id} onChange={(e) => set("collection_id", e.target.value)}>
          <option value="">All collections</option>
          {collections.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.card_count})</option>)}
        </Select>
      </div>

      <FormError message={error} />

      {!page ? (
        <div className="space-y-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-20" />)}</div>
      ) : page.items.length === 0 ? (
        <Card className="py-12 text-center">
          <p className="font-display text-xl">{filtering ? "No matches" : "Your word list is empty"}</p>
          <p className="mt-2 text-sm text-muted">
            {filtering ? "Try a different search or clear the filters." : "Add the first German word you want to remember."}
          </p>
          {!filtering && <Button className="mt-5" onClick={() => setEditing("new")}><Plus className="h-4 w-4" /> Add word</Button>}
        </Card>
      ) : (
        <ul className="space-y-2">
          {page.items.map((c) => {
            const gs = grammarSummary(c);
            const article = c.part_of_speech === "noun" ? (c.grammar as any)?.article : null;
            return (
              <li key={c.id}>
                <Card className="flex items-start gap-4 p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline gap-x-2">
                      <span className="font-display text-xl" lang="de">
                        {article && <span className="text-muted">{article} </span>}{c.term}
                      </span>
                      <span className="text-sm text-muted">{c.translations.en}{c.translations.hi && ` · ${c.translations.hi}`}</span>
                    </div>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <Badge>{c.part_of_speech}</Badge>
                      {c.cefr_level && <Badge>{c.cefr_level}</Badge>}
                      {c.sense_key && <Badge>{c.sense_key}</Badge>}
                      {gs && <span className="text-xs text-muted" lang="de">{gs}</span>}
                    </div>
                    {c.source_sentence && <p className="mt-2 truncate text-sm italic text-muted" lang="de">„{c.source_sentence}“</p>}
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <Button variant="ghost" size="icon" onClick={() => setEditing(c)} aria-label={`Edit ${c.term}`}><Pencil className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon" onClick={() => remove(c)} aria-label={`Delete ${c.term}`}><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </Card>
              </li>
            );
          })}
        </ul>
      )}

      {page && pages > 1 && (
        <div className="flex items-center justify-center gap-3 text-sm">
          <Button variant="secondary" size="sm" disabled={filters.page <= 1}
                  onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}><ChevronLeft className="h-4 w-4" /> Previous</Button>
          <span className="tabular-nums text-muted">Page {filters.page} of {pages}</span>
          <Button variant="secondary" size="sm" disabled={filters.page >= pages}
                  onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>Next <ChevronRight className="h-4 w-4" /></Button>
        </div>
      )}

      {editing && (
        <CardEditor
          card={editing === "new" ? null : editing}
          collections={collections}
          showHindi={user.preferences.show_hindi}
          onClose={closeEditor}
          onSaved={() => {
            closeEditor();
            load();
            api.collections().then(setCollections).catch(() => {});
          }}
        />
      )}
    </div>
  );
}
