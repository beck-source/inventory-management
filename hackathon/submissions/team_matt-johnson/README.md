# Team Matt

## Participants
- Matt Johnson (PM, Architect, Developer, Data Engineer — all roles, solo)

## Scenario
**Wildcard**: Went off-script. Forked an open-source geospatial intelligence platform and extended it with real-time Singapore transport data.

## What We Built
Forked **WorldView OSS** — a real-time 3D globe intelligence dashboard (CesiumJS + Next.js 16 + Zustand) — and added a **10th data layer: Singapore Carpark Availability**. The layer pulls real-time data from the LTA DataMall API, showing 129+ carparks across Singapore as color-coded dots (green/amber/red by available lots) with a natural heatmap overlay created by overlapping semi-transparent ellipses.

The implementation follows the exact 6-file architecture pattern established by the 9 existing layers (flights, satellites, disasters, etc.): API fetcher with pagination, Next.js API route with server-side caching, client-side polling hook, Zustand state management, CesiumJS entity rendering, and sidebar toggle integration. The carpark data refreshes every 60 seconds.

Everything runs. Toggle "SG Carparks" in the sidebar, fly to Singapore, and you see real-time parking pressure zones light up across the island. Red clusters in the CBD during business hours, green in suburban HDB estates.

## Challenges Attempted
| # | Challenge | Status | Notes |
|---|---|---|---|
| 1 | Fork & run WorldView OSS on macOS (ARM) | Done | Fixed Linux-only `@next/swc` dependency |
| 2 | Research Singapore real-time data sources | Done | LTA DataMall: taxis, MRT crowds, carparks, traffic |
| 3 | Add CarPark layer (full 6-file pattern) | Done | 129+ carparks, color-coded dots + heatmap ellipses |
| 4 | LTA API pagination & location parsing | Done | Handles $skip pagination, "lat lon" string parsing |
| 5 | Heatmap effect via overlapping ellipses | Done | 500m radius, 12-18% alpha, blends naturally in dense areas |

## Key Decisions
1. **Carparks over taxis** — Taxis would have been more visually dramatic (thousands of GPS dots) but carparks offered clearer color semantics (green/amber/red) and the heatmap effect. See `/decisions/001-carpark-layer-architecture.md`.
2. **Absolute lot thresholds, not percentages** — LTA API doesn't provide total capacity, only available lots. Used fixed thresholds (>100/20-100/<20) rather than building a static capacity lookup table.
3. **Followed existing patterns exactly** — Rather than inventing new architecture, replicated the exact 6-file pattern of the 9 existing layers. This makes the code instantly reviewable by anyone familiar with the codebase.

## How to Run It
```bash
# Prerequisites: Node.js 18+, free Cesium Ion token, free LTA DataMall API key
git clone https://github.com/matthewgjohnson/worldview_oss.git
cd worldview_oss
npm install

# Create .env.local with your tokens
echo 'NEXT_PUBLIC_CESIUM_ION_TOKEN=your_cesium_token' > .env.local
echo 'LTA_DATAMALL_KEY=your_lta_key' >> .env.local

npm run dev
# Open http://localhost:3000
# Toggle "SG Carparks" in sidebar, navigate to Singapore
```

## If We Had Another Day
1. **Add taxi layer** — LTA `Taxi-Availability` returns real-time GPS positions of all available taxis. Thousands of green dots swarming across Singapore would be the visual showstopper.
2. **MRT crowd density** — Color-coded station markers using `PCDRealTime` endpoint.
3. **Carpark capacity lookup** — Integrate a static dataset of total carpark capacity to show percentage-based colors instead of absolute lot counts.
4. **Singapore Quick Nav button** — Add "SG" to the Quick Nav section for one-click flyTo.
5. **Historical parking patterns** — Cache and replay carpark data over time using the timeline slider.

## How We Used Claude Code
- **Codebase exploration** — Used `Explore` agent to deeply understand the 6-file layer pattern across 9 existing layers before writing any code. This meant the implementation was right the first time.
- **Parallel research** — Launched concurrent agents to research LTA DataMall APIs AND explore the WorldView architecture simultaneously. Saved significant time.
- **AskUserQuestion** — Used interactive questions with ASCII previews for design decisions (sidebar theme for the inventory management warmup exercise).
- **Plan mode** — Designed the full implementation plan before writing code, caught the pagination requirement and location parsing edge cases upfront.
- **Environment setup** — Claude installed Node.js, uv, and gh CLI, authenticated GitHub, forked repos, and managed dev servers throughout.
- **What surprised me** — Claude's ability to read an unfamiliar codebase and replicate its patterns exactly. The carpark layer follows the same architecture as the other 9 layers without any custom scaffolding.
