---
name: application-ship-check
description: Ship-ready review to run before marking any change as done. Assesses scope and risk, UI and translation consistency across pages, API contracts and error handling, security-sensitive areas (auth, PII, secrets), and produces concrete test ideas. Use when finishing a feature or fix, before opening a PR, or when asked "is this ready to ship?"
---

# Application Ship Check

A structured, app-agnostic review that runs before a change is called done. The goal is to catch what normal self-review misses: inconsistent pages, broken contracts, missing translations, security regressions, and untested paths.

Output a report, not a code change. Only fix issues if the user asks you to.

## Step 0: Gather context

1. Find the change set:
   - `git status` and `git diff` (unstaged + staged), and `git diff <base>...HEAD` if on a branch (base is usually `main`).
   - If there is no git, ask the user which files changed, or compare against what was edited this session.
2. Read `references.md` in this skill folder for the app's entry points (router, API client, server entry, locales, auth). If it doesn't match the current repo, discover the equivalents (see "Discovering entry points" below) and use those.
3. Read the project's `CLAUDE.md` / `README.md` for release rules. Any rule there (for example "test evidence required" or "business impact summary in PR") becomes a checklist item in the report.

## Step 1: Scope and risk assessment

Summarize what changed and how dangerous it is.

- **Files touched**, grouped by layer: UI, client state / API client, server routes, data / schema, config / build, tests, docs.
- **Blast radius**: shared code (composables, hooks, stores, utils, base components, middleware, models) affects every consumer. Grep for importers of each changed shared module and list them.
- **Contract changes**: any change to a response shape, request params, route path, DB/JSON schema, env var, or public prop/event.
- **Unintended changes**: stray debug logs, commented-out code, unrelated formatting churn, lockfile or config edits, generated files.
- **Risk rating**: `Low` (isolated, UI-only, covered by tests), `Medium` (shared code or contract change with tests), `High` (auth, payments, data migration, schema change, or no test coverage). State the reason in one line.

## Step 2: UI consistency across pages, including translations

Check that the change looks and behaves like the rest of the app.

- **Cross-page parity**: if one page got a new pattern (filter, table column, empty state, loading spinner, number/date format), do sibling pages that show the same data need it too? List pages that now diverge.
- **Shared state**: global filters, selected locale, theme, or user context should be respected by every page that shows affected data. Flag pages that bypass the shared API client or state.
- **Translations / i18n**:
  - Every new user-visible string goes through the translation function; no hardcoded text in templates or JSX.
  - Every new key exists in **all** locale files with the same key path. Diff the key sets between locales and report missing or extra keys.
  - Check that translated text fits (long languages like German, or CJK line breaking), and that pluralization and interpolation work.
  - Currency, number, and date formatting use the app's locale-aware helpers, not manual formatting.
- **States**: loading, empty, error, and partial-data states exist and match other pages.
- **Design system**: colors, spacing, typography, and components match existing conventions (check the project's design notes). No one-off styles when a shared class or component exists.
- **Accessibility basics**: labels on inputs, alt text, button vs link semantics, keyboard reachability of new controls, sufficient contrast.
- **Lists and keys**: stable, unique keys for rendered lists (not array index when items can reorder).

## Step 3: API contracts and error handling

- **Client ↔ server match**: for every API call the change adds or modifies, confirm the route exists on the server with the same method, path, params, and body shape. Flag client calls to endpoints that don't exist.
- **Schema / model sync**: response models, types, or validators are updated alongside data changes. Optional vs required fields are correct.
- **Backward compatibility**: renamed or removed fields, changed types, or changed defaults that could break other consumers.
- **Input validation**: bad IDs, invalid enum values, malformed dates, empty strings, out-of-range numbers. The server should return a clear 4xx, not a 500.
- **Error responses**: consistent status codes and error body shape (404 for missing resources, 422/400 for bad input). No stack traces or internal details leaked.
- **Client error handling**: every request has a failure path (catch, error state in the UI, retry, or message). No unhandled promise rejections. No silent failures that leave the UI in a loading state forever.
- **Edge cases in data**: null or missing fields, empty arrays, division by zero in aggregates, timezone and date-boundary issues, very large lists (pagination).
- **Hardcoded values**: base URLs, ports, years, exchange rates, or feature flags that should be configurable.

## Step 4: Security-sensitive areas

Check anything touching trust boundaries. Rate each finding `Critical`, `High`, `Medium`, or `Low`.

- **Authentication and authorization**: new routes or pages are protected like their siblings; no authorization check done only on the client; no role or permission bypass through direct URLs or API calls.
- **PII and sensitive data**: names, emails, addresses, phone numbers, payment info, and IDs are not logged, not exposed in URLs or query strings, not over-returned in API responses, and not stored in localStorage unless intended.
- **Secrets**: no API keys, tokens, passwords, internal hostnames, or private registry URLs in code, config, fixtures, or commits. Check `.env` handling and `.gitignore`. Be extra strict if the repo is public.
- **Injection and XSS**: no raw HTML rendering of user or API data (`v-html`, `dangerouslySetInnerHTML`, `innerHTML`) without sanitization; parameterized queries; no shell or `eval` with user input.
- **Transport and CORS**: CORS is not widened to `*` with credentials; cookies have correct flags; no mixed content.
- **Dependencies**: newly added packages are well known, pinned appropriately, and pulled from the intended registry.
- **Mocked or stubbed security**: if auth is mocked for a demo, say so explicitly and confirm the change doesn't assume real auth exists.

If the repo defines a security-auditor subagent, consider delegating this step to it for large diffs.

## Step 5: Concrete test ideas

Produce specific, runnable test ideas tied to this change, not generic advice. For each idea give: **what**, **where** (file or test type), and **expected result**.

- **Backend / API tests**: happy path, each filter or param, invalid input (expect 4xx), not found (expect 404), empty result, and response-shape assertions for new fields.
- **Frontend / E2E checks**: navigate to each affected page, apply the relevant filters, switch locale and confirm translations and currency, and confirm loading, empty, and error states. If Playwright or another browser tool is configured, write these as browser steps.
- **Regression checks**: pages and consumers identified in the blast radius (Step 1) still work.
- **Security tests**: unauthorized access attempts, injection strings in inputs, and PII absent from responses and logs.
- Run the existing test suite and include the actual result (pass/fail counts). If tests can't be run, say why.

## Report format

```markdown
# Ship Check: <short change description>

**Verdict:** Ship | Ship with follow-ups | Do not ship
**Risk:** Low | Medium | High (one-line reason)

## 1. Scope and Risk
- Changed: ...
- Blast radius: ...
- Contract changes: ...

## 2. UI Consistency and Translations
- [ ] / [x] findings with file:line

## 3. API Contracts and Error Handling
- findings with file:line

## 4. Security
- [Severity] finding with file:line and fix suggestion

## 5. Test Ideas
| # | What | Where | Expected |
|---|------|-------|----------|

## Test Evidence
- Command run and result, or "not run: <reason>"

## Release Checklist (from project rules)
- [ ] ...

## Blocking Issues
1. ... (must fix before ship)

## Follow-ups
1. ... (safe to defer)
```

## Rules for the review

- Cite `file:line` for every finding. No finding without evidence.
- Separate **blocking** issues (bugs, security, broken contracts, missing translations for shipped locales) from **follow-ups** (polish, pre-existing gaps).
- Mark pre-existing problems as "pre-existing" so they don't block the current change unless it makes them worse.
- Don't mark anything as verified that you didn't actually check or run.
- Keep the report proportional: a one-line CSS fix gets a short report; a new feature gets the full one.

## Discovering entry points (for other apps)

If `references.md` doesn't match the repo, locate these and note them in the report:

| Concern | Look for |
|---------|----------|
| Client entry and router | `main.(js\|ts)`, `index.(js\|tsx)`, `router/`, `app/` or `pages/` directories |
| API client | `api.(js\|ts)`, `services/`, `lib/api`, axios or fetch wrappers |
| Server entry and routes | `main.py`, `app.py`, `server.(js\|ts)`, `routes/`, `controllers/` |
| Models and schemas | Pydantic models, ORM models, `types/`, OpenAPI spec, `schema.prisma` |
| Locales | `locales/`, `i18n/`, `messages/`, `*.json` translation files |
| Auth | `auth`, `session`, `middleware`, `guards`, `useAuth`, `AuthProvider` |
| Tests | `tests/`, `__tests__/`, `*.spec.*`, `*.test.*`, `pytest.ini`, `vitest.config.*` |
| Project rules | `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, PR templates |
