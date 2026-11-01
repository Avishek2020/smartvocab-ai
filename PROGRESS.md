# SmartVocab AI — Progress Checklist

Updated: 2026-11-01

## Phase 1 — Foundation ✅ complete

- [x] Architecture, diagrams, ER model, API contracts, AI workflow, model choices, roadmap, infra sizing (`docs/ARCHITECTURE.md`)
- [x] Monorepo layout, Docker Compose (Postgres 16 + pgvector image, Redis 7, backend, frontend)
- [x] Settings via environment variables, documented in `.env.example`
- [x] Full schema for all 20 tables: UUID PKs, timestamps, FKs, cascades, check constraints, indexes
- [x] Alembic migration `0001` with language seed (de / en / hi); upgrade ↔ downgrade verified; `alembic check` clean
- [x] Auth: register, login, logout; bcrypt; JWT in httpOnly cookie; server-side revocation via `token_version`
- [x] Rate limiting on auth (Redis, in-memory fallback), uniform error envelope, request IDs, security headers
- [x] Preferences API (explanation language, Hindi, CEFR, goals, time zone, theme) and account deletion
- [x] Vocabulary CRUD with German grammar plugin (discriminated by part of speech)
- [x] Lemma + sense duplicate detection, per-user isolation
- [x] Default + custom collections
- [x] Dashboard API computed from real data (no placeholders)
- [x] Frontend: landing, register, login, dashboard, vocabulary list + card editor, settings; light/dark; mobile
- [x] Tests: 31 backend tests (incl. settings loading from .env.example) on PostgreSQL (with and without Redis); TS typecheck; production build
- [x] End-to-end check through the Next.js proxy (register → add cards → dashboard → settings → sign out)

**Acceptance criteria met:** a new user can register, add German words with validated grammar,
organise them into collections, search them, see an accurate dashboard, change preferences,
sign out (all sessions revoked) and delete their account.

Known limitations carried forward:
- Lemma defaults to the typed term until spaCy lemmatization lands (Phase 3).
- "Due for review" counts new cards; the review screen itself arrives in Phase 7.
- Docker images were written but not built in this environment (no Docker daemon); the apps were run directly against Postgres 16 and Redis 7.

## Phase 2 — Multimodal input ⏭ next
- [ ] Object storage abstraction (S3/MinIO) + upload validation (magic bytes, size, type)
- [ ] Celery worker + `extraction_jobs` progress endpoint
- [ ] PDF (PyMuPDF) with scanned-page detection → Tesseract OCR (deu+eng)
- [ ] Images (OCR + vision-model provider interface)
- [ ] Text input, URL import (robots.txt check, readability extraction)
- [ ] DOCX, XLSX, TXT, EPUB
- [ ] Input workspace + processing status pages

## Phase 3 — AI vocabulary engine
## Phase 4 — Flashcard system
## Phase 5 — Voice intelligence
## Phase 6 — AI tutor
## Phase 7 — Smart revision
## Phase 8 — German grammar intelligence
## Phase 9 — Daily real-life learning
## Phase 10 — Production hardening
