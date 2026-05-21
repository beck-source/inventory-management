# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System — a workshop demo app. Full-stack Vue 3 + FastAPI, mock data loaded from JSON at startup (no database). Restart the server to reset state.

## Read first, every session

1. **Read [`LEARNINGS.md`](./LEARNINGS.md) before starting any work.** It records bugs already hit in this codebase and the rules that prevent them. Don't relearn them.
2. **After fixing a bug or discovering non-obvious behavior, append an entry to `LEARNINGS.md`** using the template in that file. One bug, one entry, specific.
3. **Always document non-obvious logic changes with inline comments.** If a future reader (human or model) has to step through the code to figure out *why*, the comment is missing. State the intent and the constraint that drove it — not the mechanics, the code already shows those.
4. **Always surface localhost URLs in your reply when you start a server, build a page, or open something.** Every time. Include the full clickable URL — `http://localhost:3000/restocking`, not "the restocking page." This applies to:
   - Dev servers you start (frontend, backend, docs)
   - New routes/pages you add (link directly to the new route, not just the root)
   - Generated static files served locally (`docs/architecture.html`)
   - Browser tabs you open via `Start-Process` / `xdg-open` / etc.
   - Any API endpoint you want the user to inspect (`http://localhost:8001/docs`, `http://localhost:8001/api/orders`)

   If you start multiple servers or open multiple URLs, list them all in a table so the user can scan and click. If Vite (or any other dev server) bound a non-default port because the canonical port was busy, **surface the actual bound port and call out the duplication** so the user can clean up.

5. **When a feature works, ship it — don't leave it loose on `main`.** As soon as a discrete piece of work passes its smoke test, the default is: create a feature branch, commit, push, open a PR. Don't wait to be asked. Specifically:

   1. **Branch.** `git checkout -b <type>/<short-name>` from the current base. Use Conventional-Commit-style prefixes: `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`. Never commit feature work directly to `main`.
   2. **Stage explicitly.** `git add <specific paths>` — never `git add -A` or `git add .`. The staging list is the change inventory; if you can't list the files, you don't understand the change. Skip debug screenshots, scratch files, and anything that doesn't belong in a teammate's clone.
   3. **Commit with a structured message.** Subject line: imperative, under 70 chars (`Add Restocking tab and Sia redesign`). Body: bullet sections — `Feature work:`, `UI:`, `Docs:`, `Config:`, etc. — explaining the *why*, not the file list. Always end with the `Co-Authored-By: Claude …` trailer.
   4. **Push to `origin` with upstream tracking.** `git push -u origin <branch>`. `origin` is the user's fork; `upstream` is the source repo (do NOT push to `upstream`).
   5. **Open the PR.** First try `mcp__github__create_pull_request` against `cyrilsayada/inventory-management` (the fork's `main`, not `upstream`). If GitHub MCP auth fails, fall back to opening `https://github.com/cyrilsayada/inventory-management/pull/new/<branch>` in the browser via `Start-Process`.
   6. **PR body must include a `## Summary` (3–5 bullets, what & why), a `## Test plan` (checked boxes for everything you ran), and an `## Out of scope` section if you noticed unrelated issues.**

   **Never:** force-push, rebase shared branches, push to `main`, push to `upstream`, or skip hooks (`--no-verify`). If a hook fails, fix the underlying issue and create a new commit — do not amend or bypass.

## Critical Tool Usage Rules

### Subagents (Task tool)
- **vue-expert** — **MANDATORY** for any creation or significant modification of a `.vue` file. Also for reactivity issues, Vue performance, complex client state.
- **code-reviewer** — invoke after writing significant code.
- **Explore** — for codebase navigation and pattern questions.
- **general-purpose** — multi-step tasks that don't fit the others.

### Skills
- **backend-api-test** — required when writing or modifying tests under `tests/backend/` (pytest + FastAPI TestClient).

### MCP Tools
- **GitHub MCP** (`mcp__github__*`) — use for ALL GitHub operations except local branch creation (`git checkout -b`).
- **Playwright MCP** (`mcp__playwright__*`) — use for browser testing. Targets: `http://localhost:3000` (UI), `http://localhost:8001` (API).

### Nested guidance
`server/CLAUDE.md` and `client/CLAUDE.md` contain detailed backend/frontend conventions. Consult them before non-trivial changes in those subtrees.

## Commands

### Run dev servers
Shell scripts (`scripts/start.sh`, `scripts/stop.sh`) are macOS/Linux only. On Windows, run each command in its own terminal.

```bash
# Backend (port 8001, docs at /docs)
cd server
uv venv && uv sync         # first time only
uv run python main.py

# Frontend (port 3000)
cd client
npm install                 # first time only
npm run dev
```

### Tests (backend only — no frontend test suite configured)
Tests live in `tests/` and run from that directory. `tests/pytest.ini` sets `testpaths = backend` and discovers `test_*.py` / `Test*` classes / `test_*` functions.

```bash
cd tests
uv run pytest                                                       # all tests
uv run pytest backend/test_inventory.py                             # one file
uv run pytest backend/test_inventory.py::TestInventoryEndpoints     # one class
uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory  # one test
uv run pytest --cov=../server --cov-report=html                     # with coverage
```

### Production build
```bash
cd client
npm run build               # outputs to client/dist/
```

## Secrets & environment variables

- **The key lives in `inventory-management/.env`** (gitignored). Template: `.env.example` (committed, never put real values there).
- The user maintains `.env` manually — **do not edit `.env`** unless explicitly asked.
- **Always read secrets from `.env`. Never hardcode keys, never print them, never echo them in commands, never commit them.** If a key appears in a shell command, redact it in any output you produce.
- **Currently stored:** `ANTHROPIC_API_KEY` — used by any Claude API call from this workspace (Basecamp notebooks, scripts, future agent code). Not used by the inventory app itself.
- **How to use it in code:**
  - Python: `from dotenv import load_dotenv; load_dotenv(); os.environ["ANTHROPIC_API_KEY"]` (add `python-dotenv` to deps if needed).
  - Shell (bash/git-bash): `set -a; source .env; set +a` then `$ANTHROPIC_API_KEY` is available.
  - Shell (PowerShell): `Get-Content .env | ForEach-Object { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') } }`.
  - Jupyter (Basecamp notebooks): the notebooks have a dedicated cell — paste from `.env`, don't commit the notebook with the key inline.
- **Adding a new variable:** add it to `.env.example` with an empty value AND to this section of CLAUDE.md. The user fills it in their local `.env`.

## Architecture

### High-level shape
A static Vue SPA in `client/` talks to a FastAPI service in `server/` over `http://localhost:8001/api/*`. Both run in dev mode; the SPA uses Vite, the API uses uvicorn invoked from `main.py`. CORS is fully open (`allow_origins=["*"]`) — fine for the workshop, not production.

There is no database, no auth, no migrations. Mock data is JSON files loaded into module-level Python lists at server startup. Mutations don't persist across restarts.

### Backend (`server/`) — single-file FastAPI

```
server/
├── main.py            # ALL endpoints + Pydantic models + filter helpers (single file)
├── mock_data.py       # Loads data/*.json once at import time into module-level lists
├── generate_data.py   # One-off script to regenerate the JSON fixtures
├── pyproject.toml     # uv-managed deps: fastapi, uvicorn, pydantic (+ pytest dev)
└── data/              # 7 JSON files, see below
```

**`data/` → endpoint mapping:**
- `inventory.json` → `/api/inventory`, `/api/inventory/{id}`
- `orders.json` → `/api/orders`, `/api/orders/{id}`
- `demand_forecasts.json` → `/api/demand`
- `backlog_items.json` → `/api/backlog`
- `spending.json` → `/api/spending/*` (file has 3 nested keys: `spending_summary`, `monthly_spending`, `category_spending`)
- `transactions.json` → `/api/spending/transactions`
- `purchase_orders.json` → consumed by dashboard/spending logic
- All data is anchored around **September 2025**.

**Two shared filter helpers in `main.py` are the backbone of every endpoint:**
- `apply_filters(items, warehouse, category, status)` — sequential filtering, skips any value equal to `'all'`, case-insensitive on `category` and `status`.
- `filter_by_month(items, month)` — supports either a direct `YYYY-MM` substring match on the item's `order_date` field, OR a quarter key (`Q1-2025`…`Q4-2025`) via the `QUARTER_MAP` constant. Quarters are **2025-only**; extending years means updating the map.

**Adding an endpoint:** define a Pydantic response model in `main.py`, write the function, decorate with the route, run filters via the two helpers, return the model. Then add tests in `tests/backend/test_*.py` using the `client` fixture from `conftest.py`.

### Frontend (`client/`) — Vue 3 + vue-router + axios, no state library

```
client/src/
├── main.js          # App entry — defines router with 6 routes (see below)
├── App.vue          # Root component + global styles
├── api.js           # Single axios client; ALL HTTP goes through here
├── views/           # Page-level components, one per route
├── components/      # Reusable UI (FilterBar, *DetailModal, ProfileMenu, etc.)
├── composables/     # Shared logic + module-scoped reactive state
├── utils/           # Pure helpers
└── locales/         # i18n strings (consumed by useI18n.js)
```

**Routes (`main.js`):**
| Path         | View              |
|--------------|-------------------|
| `/`          | `Dashboard.vue`   |
| `/inventory` | `Inventory.vue`   |
| `/orders`    | `Orders.vue`      |
| `/demand`    | `Demand.vue`      |
| `/spending`  | `Spending.vue`    |
| `/reports`   | `Reports.vue`     |

**State strategy — singleton refs in composables.** There's no Pinia/Vuex. Shared state lives at the *top of the composable file* (outside the exported function), so all components calling the same composable see the same refs. Example: `useFilters.js` declares `selectedPeriod`, `selectedLocation`, `selectedCategory`, `selectedStatus` at module scope — every view binds to the same filter values.

⚠️ **Naming mismatch worth knowing:** in the UI/composable the warehouse filter is called `selectedLocation`, but `getCurrentFilters()` emits it as `warehouse` for the API. Keep the API key as `warehouse` to stay aligned with the backend.

**Composables present:**
- `useFilters.js` — global filter selection (`Period`/`Location`/`Category`/`Status`), `hasActiveFilters`, `resetFilters`, `getCurrentFilters` (returns the API-shaped object).
- `useAuth.js` — auth state (demo only, no real backend auth).
- `useI18n.js` — translation lookup against `src/locales/`.

### End-to-end data flow
1. User toggles a filter in `FilterBar.vue` → mutates a ref in `useFilters.js`.
2. View's `loadData()` calls `getCurrentFilters()` → passes to `api.js`.
3. `api.js` builds `URLSearchParams`, **omitting any value equal to `'all'`**, and `axios.get`s the endpoint.
4. FastAPI endpoint runs `apply_filters` and/or `filter_by_month` over the in-memory list.
5. Returns Pydantic-validated JSON.
6. View stores raw response in a `ref`; computed properties derive display data (totals, sorted lists, chart series).

### Filter contract (memorize this)
Four filters span the whole app — **Period**, **Warehouse** (`selectedLocation` in UI), **Category**, **Order Status** — all optional query params.
- Both client and server treat the string `'all'` as "no filter."
- Inventory has no time dimension, so `month` is **ignored** by `/api/inventory`.
- Quarter values must match `QUARTER_MAP` keys exactly (`Q1-2025`, `Q2-2025`, `Q3-2025`, `Q4-2025`).
- Category/status comparisons are case-insensitive; warehouse is case-sensitive.

## API Endpoints
- `GET /api/inventory` — filters: `warehouse`, `category`
- `GET /api/inventory/{id}` — 404 on miss
- `GET /api/orders` — filters: `warehouse`, `category`, `status`, `month`
- `GET /api/orders/{id}` — 404 on miss
- `GET /api/dashboard/summary` — all filters
- `GET /api/demand`, `GET /api/backlog` — no filters
- `GET /api/spending/summary`, `/api/spending/monthly`, `/api/spending/categories`, `/api/spending/transactions`

## Repo-specific gotchas (the short list — full history in `LEARNINGS.md`)
1. **Never use array index for `:key`** in `v-for` — use `sku`, `id`, `month`, etc. Index keys cause Vue to reuse DOM nodes incorrectly when lists change.
2. **Validate dates before `.getMonth()`** — `new Date('invalid').getMonth()` returns `NaN` and silently breaks downstream filters. Check `!isNaN(date.getTime())` first.
3. **Update Pydantic models when `server/data/*.json` schema changes** — silent field drop otherwise (FastAPI excludes unknown fields from the response).
4. **Inventory endpoints reject month filtering** — passing `month=...` to `/api/inventory` is a silent no-op.
5. **Revenue goals are hard-coded**: $800K/month single-month, $9.6M YTD across all months. Search for these constants before changing them in any one place.
6. **Auth is fake.** `useAuth.js` is UI scaffolding only. Do not gate any real logic on it.

## Design system
- Slate/gray palette: `#0f172a`, `#64748b`, `#e2e8f0`
- Status colors: green / blue / yellow / red
- Charts: hand-rolled SVG; layouts: CSS Grid
- No emojis in UI
