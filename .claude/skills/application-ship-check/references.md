# Application Entry Points

Starting points for the ship check. The first table is for this repository (Factory Inventory Management System). When reusing the skill in another app, replace these tables with that app's equivalents, or use the "Discovering entry points" table in `SKILL.md`.

## Frontend (Vue 3 + Vite, port 3000)

| Concern | File | Why it matters |
|---------|------|----------------|
| App bootstrap and router | `client/src/main.js` | Route list; any view not registered here can't be reached |
| Root layout and global styles | `client/src/App.vue` | Nav, global CSS, tasks feature wiring |
| API client | `client/src/api.js` | All HTTP calls; base URL; drops `'all'` filter params |
| Shared filter state | `client/src/composables/useFilters.js` | Singleton filters used by every page; `getCurrentFilters()` maps to API params |
| i18n | `client/src/composables/useI18n.js` | `t('dot.path')`, locale persisted in localStorage `app-locale` |
| Locale dictionaries | `client/src/locales/en.js`, `client/src/locales/ja.js` | Keys must match in both |
| Currency formatting | `client/src/utils/currency.js` | USD to JPY at a fixed rate; use helpers, never format by hand |
| Auth (mocked) | `client/src/composables/useAuth.js` | Hardcoded user; no real auth |
| Pages | `client/src/views/*.vue` | Check cross-page consistency here |
| Shared components | `client/src/components/*.vue` | `FilterBar.vue`, modals, `LanguageSwitcher.vue`, `ProfileMenu.vue` |
| Build config | `client/vite.config.js`, `client/package.json`, `client/.npmrc` | Port, deps, public registry pin |

## Backend (FastAPI, port 8001)

| Concern | File | Why it matters |
|---------|------|----------------|
| Server entry, routes, models | `server/main.py` | Single file: Pydantic models, `apply_filters`, `filter_by_month`, all endpoints, CORS |
| Data loading | `server/mock_data.py` | Loads `server/data/*.json` once at import |
| Data | `server/data/*.json` | Changing shapes requires updating Pydantic models |
| Dependencies | `server/pyproject.toml` | Runtime and dev (pytest) deps |

## Tests

| Concern | File |
|---------|------|
| Config | `tests/pytest.ini` |
| Fixtures (TestClient) | `tests/backend/conftest.py` |
| API tests | `tests/backend/test_inventory.py`, `test_dashboard.py`, `test_misc_endpoints.py` |
| Run | `cd tests && uv run --project ../server pytest` |

## Project Rules and Tooling

| Concern | File |
|---------|------|
| Release standards and conventions | `CLAUDE.md`, `client/CLAUDE.md`, `server/CLAUDE.md` |
| Subagents (code-reviewer, security-auditor, vue-expert) | `.claude/agents/` |
| MCP servers (Playwright, GitHub) | `.mcp.json` |
| Start/stop scripts | `scripts/start.sh`, `scripts/stop.sh` |

## Known Hotspots in This Repo

- `client/src/api.js` calls `/api/tasks` and `/api/purchase-orders`, which don't exist in `server/main.py`.
- `client/src/views/Reports.vue` calls the API with axios directly, so it skips `api.js` and the shared filters.
- `client/src/views/Backlog.vue` isn't registered in the router.
- Quarters (`QUARTER_MAP` in `server/main.py`) and the JPY rate (`client/src/utils/currency.js`) are hardcoded.
