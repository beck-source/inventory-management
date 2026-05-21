# Security Audit Findings — inventory-management

Auditor: security-auditor (inventory-audit team)
Date: 2026-05-21
Scope: `server/main.py`, `server/mock_data.py`, `client/src/**`, dependency manifests, `.env*`.

**Context:** This is a workshop/demo app — no DB, no real auth, mock data, single-host dev only. The README and CLAUDE.md explicitly state "Auth is fake" and "CORS allows all origins — fine for the workshop, not production." Findings below are **calibrated to that posture**: I do not flag the absence of auth as a vuln. I flag code paths that would become foot-guns if this demo were ever promoted toward production, plus the few issues that bite even in demo mode.

---

## 1. CORS `allow_origins=["*"]` combined with `allow_credentials=True`
- **Severity:** High (latent — Medium in current demo posture, but the misconfiguration is real today)
- **Location:** `server/main.py:51-57`
- **Description:** `CORSMiddleware` is configured with `allow_origins=["*"]` AND `allow_credentials=True`. The FastAPI/Starlette implementation will silently reject credentialed requests from `*` per the CORS spec, so today the demo "works" only because no cookies/auth headers are sent. The moment real auth (cookies, `Authorization` header treated as credential) is added, every browser becomes a confused-deputy proxy: any malicious origin can issue authenticated requests against `localhost:8001` running in the user's session. This is the classic "fully open + credentialed" mistake and it will not be caught at runtime — it just becomes exploitable as soon as creds appear.
- **Fix:** Either set `allow_credentials=False` for the demo, OR replace `allow_origins=["*"]` with an explicit list (`["http://localhost:3000"]`). Do this *now*, not "when we add auth" — it removes a footgun before real auth lands.

## 2. No size/length/range validation on Pydantic request models
- **Severity:** Medium
- **Location:** `server/main.py:99-143` (`RestockOrderItemPayload`, `RestockOrderPayload`, `CreatePurchaseOrderRequest`)
- **Description:** Models accept arbitrarily large strings, arbitrarily long item lists, negative quantities, negative unit prices, NaN/Infinity floats, and unbounded `notes`/`supplier_name`. `POST /api/orders` will happily accept `items: [...100k entries...]` and append to the in-memory `orders` list (DoS via memory growth). `quantity=-5` is accepted; `unit_price=-1` is accepted; `unit_price=1e308` is accepted (will overflow `total_value` calculations downstream). No `max_length` on string fields means a 10MB `customer` string is accepted and echoed back.
- **Fix:** Add Pydantic constraints — `quantity: int = Field(ge=1, le=100000)`, `unit_price: float = Field(ge=0, le=1e7)`, `customer: Optional[str] = Field(default="Internal Restock", max_length=200)`, `items: List[...] = Field(min_length=1, max_length=500)`. Likewise on `CreatePurchaseOrderRequest`.

## 3. `POST /api/orders` mutates shared in-memory state with no rate limiting or ownership check
- **Severity:** Medium (in demo); High if ever promoted
- **Location:** `server/main.py:178-228`
- **Description:** Any caller (no auth required — by design) can submit unlimited orders that mutate the module-level `orders` list. Combined with finding #2 this is a trivial memory-exhaustion vector. There is also no idempotency key, so retries duplicate. Because `new_id = str(len(orders) + 1)`, a concurrent burst can produce duplicate IDs (race on `len`). For a demo this is annoying; the moment this code is reused with real persistence, duplicate primary keys and unbounded growth carry over.
- **Fix:** Add a per-IP request cap (e.g., `slowapi`); compute IDs from a counter or UUID, not list length; bound the list size (`if len(orders) > N: raise 429`).

## 4. Frontend trusts `useAuth.isAuthenticated = ref(true)` — no router guard, but also no real decision gated on it
- **Severity:** Low (informational — README warns this is fake)
- **Location:** `client/src/composables/useAuth.js:92`, used in `client/src/components/ProfileMenu.vue`
- **Description:** `isAuthenticated` is hardcoded `true` and exported. I checked every usage: nothing in `views/`, `router`, or `api.js` makes a security-relevant decision based on this value (only `ProfileMenu` reads `currentUser` for display). This finding exists to **lock that property in**: if anyone later writes `if (isAuthenticated.value) { ... do sensitive thing ... }`, they will get a false sense of security. Add a code comment, or rename to `isAuthenticatedMock`, so the trap is visible.
- **Fix:** Rename the ref to `isAuthenticatedMock` and add a `// DO NOT GATE LOGIC ON THIS — see CLAUDE.md` comment at line 92. Costs nothing, prevents a future bug.

## 5. Stack traces & internal details leakage via default FastAPI error handling
- **Severity:** Low
- **Location:** `server/main.py` (no global exception handler defined)
- **Description:** FastAPI in dev mode returns full Python tracebacks on unhandled exceptions, exposing file paths (`C:\Users\CyrilSAYADA\...`), library versions, and code structure. Trigger examples: `GET /api/orders/{order_id}` with a malformed ID type doesn't crash (typed as `str`), but `POST /api/orders` with `unit_price=1e308` then `total_value` rounding can raise; any future endpoint touching `KeyError` on `item.get('warehouse')` after schema drift will dump traceback. For a localhost demo this just leaks the absolute path of the workshop user's home directory (which can include their AzureAD username — see absolute path above).
- **Fix:** Add `@app.exception_handler(Exception)` that returns `{"detail": "Internal server error"}` with 500, log full details server-side only. Cheap; eliminates a class of disclosure.

## 6. Path-traversal risk surface — currently NONE, by construction
- **Severity:** Informational (negative finding worth recording)
- **Location:** `server/main.py`, `server/mock_data.py:14-18`
- **Description:** I checked every `open(`, `StaticFiles`, `FileResponse`, and path-joining call. The only file I/O is `mock_data.load_json_file()`, which receives **hardcoded filenames** from module-level code — no user input flows into a filesystem path. No `/api/files/...` style endpoint exists. Recording this so the next auditor doesn't re-investigate.
- **Fix:** None needed. If a future endpoint adds file serving, validate paths with `Path.resolve().is_relative_to(DATA_DIR)`.

## 7. Verbose console logging in production builds (Reports.vue)
- **Severity:** Low
- **Location:** `client/src/views/Reports.vue` — 12 `console.log` calls between lines 145-256
- **Description:** Not a secret-leak per se (no tokens are logged — confirmed by grepping `token|password|secret|api[_-]?key`), but the volume of `console.log('Fetching quarterly data...')`, `console.log('Quarterly data:', this.quarterlyData)`, etc. ships in the production Vite bundle by default and exposes full API response shapes in the browser console. Anyone with DevTools — including a malicious browser extension reading console output — sees the full revenue/order dataset. Low severity because the same data is fetched via observable XHR anyway, but the noise is unprofessional and increases attack surface for log-scraping extensions.
- **Fix:** Strip `console.log` in production via `vite.config` `esbuild: { drop: ['console'] }`, or replace with a `debug()` helper gated on `import.meta.env.DEV`.

## 8. Frontend calls `/api/tasks`, `/api/tasks/{id}`, `/api/purchase-orders*` — endpoints that do NOT exist on the server
- **Severity:** Low (bug, not a vuln — but security-adjacent)
- **Location:** `client/src/api.js:84-112` vs `server/main.py` (no matching routes)
- **Description:** The client confidently issues `GET /api/tasks`, `POST /api/tasks`, `DELETE /api/tasks/{id}`, `PATCH /api/tasks/{id}`, `POST /api/purchase-orders`, and `GET /api/purchase-orders/{id}`. None exist server-side. Today every call 404s and is swallowed by `console.error`. The security relevance: when these endpoints *are* added, whoever writes them will have no spec to follow and will likely skip the validation work flagged in #2. I'm flagging here to nudge the eventual implementer to apply the same Pydantic constraints.
- **Fix:** Either remove the dead client code, or stub the endpoints server-side with the proper Pydantic validators in place from day one.

## 9. Dependency versions — no obvious knowns-bad, but pinning is loose
- **Severity:** Informational
- **Location:** `server/pyproject.toml`, `client/package.json`
- **Description:** All deps use `>=` (Python) or `^` (npm) — fine for a demo, predictable supply-chain drift in CI. Versions present (`fastapi>=0.110.0`, `vue ^3.4.21`, `axios ^1.6.7`, `vite ^5.2.0`) have no current known critical CVEs I'd block release on. `axios <1.7.4` has had a couple of SSRF/CRLF issues fixed; `^1.6.7` will float forward on `npm install`, which is the right behavior.
- **Fix:** Commit `package-lock.json` and `uv.lock` (currently the latter is gitignored — see `.gitignore:31` `*.lock` — actively bad for reproducible builds; reconsider).

---

## Top 3 must-fix (for consolidation)

1. **Finding #1** — Fix CORS `allow_credentials=True` with wildcard origins. Five-line change, eliminates a latent High.
2. **Finding #2** — Add Pydantic `Field` constraints (length, range, list size) to the three POST models. Cheap, prevents DoS and downstream overflow.
3. **Finding #4** — Rename `isAuthenticated` → `isAuthenticatedMock` and add an inline comment. Five-second change, prevents the most plausible future bug class (someone gating real logic on the fake flag).
