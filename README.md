# SmartVocab AI

AI-powered multimodal vocabulary learning — German first, explained in English and Hindi.

**Status: Phase 1 (Foundation) complete.** See [PROGRESS.md](PROGRESS.md) for the phase checklist and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architecture, ER diagram, API contracts, AI workflow,
model choices, roadmap and infrastructure sizing.

## What works today

- Registration, login, logout (revokes every session), account deletion
- Preferences: explanation language (EN/HI), Hindi toggle, CEFR level, daily goals, time zone, theme
- Manual vocabulary cards with German grammar validated per part of speech
  (article/plural/genitive for nouns; Präteritum, Partizip II, haben/sein, separable prefix,
  reflexive, preposition + case for verbs; comparative/superlative for adjectives)
- Same word, different meaning: cards are unique per lemma **and sense** (Bank = bench vs. bank)
- 12 default collections per user + custom collections
- Search (German or translation), filters (CEFR, part of speech, collection), pagination
- Dashboard computed entirely from your data: totals, due, mastered, difficult, streak,
  7-day activity, CEFR distribution, retention (shown as "no reviews yet" until there are reviews)
- Light/dark/system theme, mobile layout, Swagger at `/docs`

Nothing calls an AI model yet — that starts in Phase 3, behind provider interfaces configured in `.env`.

## Quick start (Docker)

```bash
cp .env.example .env            # set JWT_SECRET for anything beyond local use
docker compose up --build
```

- App: http://localhost:3000
- API docs: http://localhost:8000/docs

Migrations run automatically when the backend container starts.

## Local development (without Docker for the apps)

Prerequisites: Python 3.12+, Node 20+, PostgreSQL 16, Redis 7 (`docker compose up postgres redis` is the easiest way).

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://smartvocab:smartvocab@localhost:5433/smartvocab
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
BACKEND_URL=http://localhost:8000 npm run dev
```

The browser only talks to Next.js; `/api/v1/*` is proxied to FastAPI so the session cookie is
first-party and `httpOnly`. No tokens are ever readable from JavaScript.

## Tests

```bash
# create the test database once
createdb -U smartvocab smartvocab_test
cd backend
TEST_DATABASE_URL=postgresql+psycopg://smartvocab:smartvocab@localhost:5433/smartvocab_test pytest -q
```

31 tests run against real PostgreSQL (migrated with Alembic): auth flows, token revocation, rate
limiting, preferences validation, card CRUD, German grammar validation, duplicate detection,
search/filter/pagination, cross-user isolation and dashboard metrics.

Frontend checks: `npm run typecheck` and `npm run build` (includes ESLint).

## API testing by hand

```bash
B=http://localhost:3000/api/v1
curl -c jar -X POST $B/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"Deutsch2026ok","display_name":"Me"}'
curl -b jar -X POST $B/vocabulary -H 'Content-Type: application/json' -d '{
  "term":"teilnehmen","part_of_speech":"verb","cefr_level":"B1",
  "translations":{"en":"to take part","hi":"भाग लेना"},
  "grammar":{"infinitive":"teilnehmen","separable":true,"separable_prefix":"teil",
             "auxiliary":"haben","partizip_ii":"teilgenommen",
             "prepositions":[{"preposition":"an","case":"dativ"}]}}'
curl -b jar $B/analytics/dashboard
```

## Project layout

```
backend/   FastAPI app, SQLAlchemy models (all 20 tables), Alembic migrations, tests
frontend/  Next.js 14 (App Router) + TypeScript + Tailwind
docs/      Architecture, ER diagram, API contracts, AI workflow, roadmap
```
