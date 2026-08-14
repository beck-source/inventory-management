# Claude Code Workshop: Building the Factory Inventory Management System

## For Readers Who Weren't There

This document was written during a two-day **Anthropic Partner Basecamp** workshop (a hands-on training session for enterprise partners, ending in a team hackathon). If you weren't in the room, here's the context you need:

**What is Claude Code?** Anthropic's AI coding assistant. It runs as a desktop app, a terminal CLI, or in your IDE, and can read your codebase, write and edit code, run commands, browse the web, and more — all while following project-specific conventions you give it.

**Quick glossary** (terms used throughout this doc):

| Term | What it means |
|---|---|
| **Slash command** | A command typed directly into Claude's chat, like `/context` or `/compact` — not a terminal/bash command. |
| **MCP (Model Context Protocol)** | A connector standard that gives Claude access to external tools — e.g., the Playwright MCP gives Claude real browser control. |
| **Subagent** | A focused, specialized version of Claude scoped to a task (e.g., a Vue specialist, a security auditor) with its own instructions and tool access. Defined in `.claude/agents/`. |
| **Skill** | A reusable, packaged set of instructions Claude follows for a recurring task (e.g., "how to write backend tests," "how to optimize Vue components"). Defined in `.claude/skills/`. |
| **CLAUDE.md** | A file in the repo that tells Claude the project's conventions, rules, and patterns to follow — read automatically at the start of every session in that repo. |
| **Plan Mode** | A mode where Claude designs an approach and gets it approved *before* writing any code, useful for non-trivial features. |

---

## What We're Building

A **Factory Inventory Management System** — a web application that helps factories track:
- Inventory levels across warehouses
- Customer orders and their status
- Demand forecasts
- Revenue and spending
- Backlog (orders waiting to be fulfilled)

The app has two parts:
1. **Frontend** (what you see) — A dashboard in your browser showing charts, tables, and metrics (Vue 3)
2. **Backend** (the invisible part) — A server that stores data and sends it to the frontend when requested (Python/FastAPI)

---

## Steps Completed

### ✅ Step 1: Fork & Clone Repository (10 pts)
**What we did:**
- Forked the original inventory app from Anthropic's GitHub to a personal GitHub account
- Cloned it locally to `/Users/moukie/Claude/inventory-management`
- Created a working branch called `new_features` to make changes safely

**Why:** A personal copy that can be modified without affecting anyone else's work.

---

### ✅ Step 2: Launch Claude Code (10 pts)
**What we did:**
- Opened Claude Code and selected a model

**Why:** Claude Code is the tool used to write, understand, and modify code throughout the workshop.

---

### ✅ Step 3: Run Inventory Management Locally (15 pts)
**What we did:**
1. Installed Node.js
2. Installed frontend dependencies (`npm install` in `client/`)
3. Installed backend dependencies (`uv sync` in `server/`)
4. Started the backend (FastAPI, port 8001)
5. Started the frontend (Vue 3 + Vite, port 3000)
6. Opened `http://localhost:3000` to see the working dashboard

**Why:** A fully running app on your machine that you can modify and test.

---

### ✅ Step 4: Edit CLAUDE.md File (5 pts)
**What we did:**
- Added a "Code Style" rule to CLAUDE.md: *"Always document non-obvious logic changes with comments"*

**Why:** CLAUDE.md is how Claude learns project conventions — every session in this repo reads it automatically.

---

### ✅ Step 5: Understand the Codebase (20 pts)
**What we did:**
- Explored the codebase and read key files (backend `main.py`, frontend `api.js`, view components)
- Generated `ARCHITECTURE.html` — a visual page explaining the Vue ↔ FastAPI ↔ mock-data flow, tech stack, API endpoints, and dashboard structure
- Opened it in the browser

**Why:** Understanding the architecture *before* building keeps new code consistent with existing patterns.

---

### ✅ Step 6: Build Budget-Based Restocking Feature (25 pts)
**What we built:** A budget-constrained restocking tool — set a budget, get AI-recommended items based on demand forecasts, adjust quantities, submit the order.

Used **Plan Mode** for this one: Claude proposed a design, asked clarifying questions (budget range, recommendation algorithm, whether quantities are adjustable, how orders integrate with the existing Orders system), and only started coding once the plan was approved.

**Backend:**
- `GET /api/restocking/recommendations?budget=X` — prioritizes items by demand gap (forecasted − current demand), fills the budget greedily
- `POST /api/restocking/orders` — creates orders with "Submitted" status and a 7-day delivery lead time
- Budget validation (rejects orders exceeding budget)

**Frontend:**
- New `Restocking.vue` view: budget slider, live stats (budget/items/cost/remaining), adjustable recommended-items table, Place Order button
- New nav tab, route, and English/Japanese translations

**A bug we caught in review:** the quantity field initially showed `0` for every recommendation — turned out the component was reading `item.recommended_quantity` but the backend actually returned `item.recommended_qty`. One-line fix once traced.

---

### ✅ Step 7: Context Management (10 pts)
**What we did:**
- Ran `/context` to see a breakdown of token usage (system prompt, tools, messages, free space)
- Ran `/compact` to summarize the conversation and free up space, keeping key details
- Used `/compact keep the details of the restocking feature` to steer *what* gets preserved during summarization

**Why:** Long sessions fill up the context window. `/compact` lets Claude keep working without losing track of what matters, and you can tell it what to prioritize.

---

### ✅ Step 8: Add Playwright MCP (15 pts)
**What we did:** Installed the Playwright MCP so Claude can control a real browser (navigate pages, click, screenshot, read console/network activity).

**What we ran into (worth knowing):** the intended command was a single line —
```
claude mcp add playwright npx @playwright/mcp@latest
```
— but the `claude` CLI wasn't on the system PATH yet. Troubleshooting took a few turns:
1. `npm install -g @anthropic-sdk/cli` → wrong package name, 404
2. `npm install -g claude` → `EACCES` permission error (npm trying to write to a protected system folder)
3. `sudo npm install -g claude` → installed *a* package, but not actually the right Claude Code binary
4. Searched the filesystem and found the real CLI bundled inside the Claude desktop app itself, at a versioned path under `~/Library/Application Support/Claude/`
5. Created a symlink (`/usr/local/bin/claude → the bundled binary`) so `claude` resolves from any terminal
6. Ran the MCP install command successfully, then **restarted Claude Code** so it picked up the new MCP config

**Why it matters:** MCP servers extend what Claude can *do* — this one turned "describe what the app should do" into "actually click through it and check."

---

### ✅ Step 9: Test the App with Playwright MCP
**What we did:**
1. Started the dev servers, opened `http://localhost:3000`
2. Screenshotted the dashboard
3. Clicked through all 7 nav tabs (Overview, Inventory, Orders, Finance, Demand Forecast, Restocking, Reports) and confirmed each rendered correctly

**The catch:** the first pass only tested navigation. When asked *"did you test everything? some filters aren't working"*, we went back and actually exercised the 4 shared filters (Time Period, Location, Category, Order Status) — setting each one and confirming the dashboard numbers actually changed. All four worked correctly; the lesson was that "the page loads" and "the feature works" are different claims, and only one of them was actually tested the first time.

**Why:** Automated browser testing catches real integration bugs (wrong data, broken filters, console errors) that a code read-through won't.

---

### ✅ Step 10: Connect Claude Code to GitHub (15 pts) — *blocked*
**What we did:**
- Learned that `/install-github-app` is a **slash command run inside an interactive Claude Code session** — not a bash command, and not available in every chat surface (it failed in a non-interactive continuation session before working in a real terminal `claude` session)
- Ran it and authorized the GitHub App on the fork

**Where it stopped:** the flow requires access to **Claude organization settings**, which are only available on Team/Enterprise plans — not a personal Pro plan. The install couldn't complete, and no workflow PR was ever generated as a result.

**Why it matters (even unfinished):** this integration is what enables `@claude` mentions in GitHub issues/PRs and automatic Claude-authored code review on every PR — genuinely useful for a team, but it needs the right plan tier. Flagged as a follow-up for whoever manages the team's Anthropic workspace.

---

### ✅ Step 11: Commit & Push
**What we did:**
- Realized Step 6's restocking work had been sitting **uncommitted** for several steps — committed it, and from that point on committed after every real code/file change (not after every workshop step — just when something actually changed)
- Pushed the `new_features` branch to the GitHub fork

**What we ran into:** pushing from this environment initially failed (`git` had no credentials configured for a non-interactive session). Pushing from an actual terminal hit a second wall — a `403 Permission denied`, traced to a personal access token that was missing the `repo` scope. Regenerating the token with the right scope fixed it.

**Note on the PR:** a pull request was attempted but never actually completed (the fork showed 0 PRs when checked afterward) — and the team decided that's fine; a PR wasn't needed to demonstrate the workflow. The important part — a clean, pushed commit history — was already in place.

---

## Beyond the Workshop: Building Custom Tools

Two custom additions to this project's `.claude/` setup, plus a real bug found and fixed using them.

### 🔧 New Skill: `vue-component-optimizer`
Lives at `.claude/skills/vue-component-optimizer/SKILL.md`. Analyzes every `.vue` file for two categories of issues, then applies the fixes:

- **Performance**: reactivity misuse (derived values that should be `computed()` but aren't), watchers doing a computed's job, unstable `v-for` keys, unmemoized expensive work, inline template literals recreated every render
- **Code reuse**: duplicated formatting logic, duplicated API-loading patterns, duplicated markup (stat cards, tables) that should be shared components, duplicated filter-handling logic

Registered in CLAUDE.md so Claude knows to reach for it automatically when asked to review or optimize Vue components.

### 🐛 New Subagent: `debugger`
Lives at `.claude/agents/debugger.md`. A **read-only** specialist (tools: Read, Grep, Glob, Bash — deliberately no Write/Edit) that investigates runtime errors:

- Parses stack traces (both Python/FastAPI and JS/Vue conventions)
- Distinguishes root cause from symptom
- Reproduces failures via Bash where possible (`curl` an endpoint, run a specific test)
- Checks whether the same bug pattern is duplicated elsewhere in the codebase
- Hands off *proposed* fixes rather than applying them — frontend fixes get routed to the `vue-expert` subagent per this project's existing convention, backend fixes get applied directly

**A caveat we found in practice:** custom subagents defined under `.claude/agents/` are picked up automatically by the *interactive* `claude` CLI (running `claude` in a terminal). This particular chat surface's agent-dispatch tool only exposes a fixed set of built-in agent types and doesn't dynamically load project-defined ones — so invoking `debugger` here required doing the same investigation directly instead of through the named subagent. Worth confirming which surface your team is using before assuming custom agents "just work."

### Case Study: Fixing Real Dashboard Console Errors
Put both new tools to work on an actual bug hunt — the Dashboard page had two live issues:

1. **`[Vue warn]: Failed to resolve component: PurchaseOrderModal`** — repeated on every render
2. **`404` on `GET /api/tasks`** on page load

**Investigation:** Grep'd for `PurchaseOrderModal` across the frontend and found it referenced in `Dashboard.vue`'s template with a full set of props and event handlers wired up — but the component file itself never existed anywhere in the codebase, and its backend counterpart (`/api/purchase-orders`) didn't exist either, despite the backend already having Pydantic models and an (empty) mock-data file scaffolded for it. This was a feature that got partially built and abandoned. Separately, `getTasks()` in the frontend's API client called `GET /api/tasks` — a route that was simply never implemented on the backend.

**Decision point:** for the PO modal, the choice was between *finishing* the abandoned feature (bigger scope — a new modal component plus new backend endpoints) or *removing* the dead code. Since the actual task was "fix the console error," not "build a purchase-order feature," the dead code was removed — template block, refs, methods, buttons, and CSS — while leaving the separate, working `BacklogDetailModal` feature untouched.

**Fixes applied:**
- Removed the orphaned `PurchaseOrderModal` usage from `Dashboard.vue` (delegated to `vue-expert`, per this repo's mandatory rule that all `.vue` edits go through it)
- Added the missing `GET` / `POST` / `PATCH` / `DELETE /api/tasks` endpoints to `server/main.py`, matching the shape the frontend already expected

**Verification:** reloaded the app in a *fresh* browser tab (to rule out stale hot-reload state) — zero console warnings, zero errors, `/api/tasks` returns `200`.

---

## How It All Connects

The pieces built across this workshop aren't independent — they compose:

- **CLAUDE.md** sets the ground rules for the whole repo (e.g., "all `.vue` edits go through `vue-expert`")
- **Subagents** (`vue-expert`, `code-reviewer`, `security-auditor`, `debugger`) are specialists Claude delegates to when a task matches their scope — CLAUDE.md is what tells Claude *which* one to reach for
- **Skills** (`backend-api-test`, `vue-component-optimizer`) package up a repeatable *process* rather than a persona — "when doing X, follow these steps"
- **MCP** (Playwright) gives Claude a way to *verify* claims instead of just asserting them — "the filters work" became "I set each filter and confirmed the numbers changed"
- **Git/GitHub workflow** is what turns local changes into something a team can actually review and build on

The debugging case study above is a small example of the whole stack working together: a real error → investigated with the same rigor a `debugger` subagent would apply → a `.vue` fix routed through `vue-expert` per CLAUDE.md's rule → verified live with the Playwright-powered browser tools → committed and pushed.

---

## Summary

**Steps completed:**
| Step | Points |
|---|---|
| 1. Fork & Clone Repository | 10 |
| 2. Launch Claude Code | 10 |
| 3. Run Locally | 15 |
| 4. Edit CLAUDE.md | 5 |
| 5. Understand the Codebase | 20 |
| 6. Budget-Based Restocking Feature | 25 |
| 7. Context Management | 10 |
| 8. Add Playwright MCP | 15 |
| 9. Test with Playwright MCP | — |
| 10. Connect to GitHub | 15 (blocked — plan tier) |
| 11. Commit & Push | — |

**Confirmed points: 125** (Steps 9 and 11 weren't shown with an explicit point value; Step 10's points reflect the step attempted, not fully completed)

**Technologies & patterns used:**
- Vue 3 Composition API (`ref`, `computed`, `watch`)
- FastAPI with Pydantic validation
- Budget-constrained recommendation algorithm
- i18n (English/Japanese)
- RESTful API design
- Git feature-branch workflow
- MCP (Playwright) for real browser verification
- Custom Claude Code skills and subagents

**Key takeaways for the team:**
1. **Plan Mode earns its keep on real features** — the restocking tool's design questions (budget range, algorithm, order integration) were resolved *before* code was written, not discovered mid-implementation.
2. **"It loads" ≠ "it works."** The filter-testing gap in Step 9 is a good reminder to verify behavior, not just rendering.
3. **CLAUDE.md is what makes delegation consistent** — the "route all `.vue` edits through vue-expert" rule kept applying correctly across completely different tasks (the restocking feature, the skill, the bug fix).
4. **Custom skills/subagents are cheap to build and genuinely reusable** — `vue-component-optimizer` and `debugger` now exist for anyone who works in this repo going forward.
5. **Plan-tier and environment limits are real** — GitHub App org settings and custom-subagent dispatch both behaved differently depending on which Claude surface (personal plan vs. Team/Enterprise; chat vs. terminal CLI) was in use. Worth checking before assuming a workflow will "just work" for the whole team.

**Note:** This guide reflects the actual session, including the parts that didn't go smoothly on the first try (permission errors, a missing PR, a plan-tier blocker) — kept in rather than cleaned up, since those are often the more useful parts for a team reading this afterward.
