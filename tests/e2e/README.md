# E2E Tests

Playwright tests for the frontend. Assumes both servers are already running
(`./scripts/start.sh`) — frontend on `http://localhost:3000`, backend on `http://localhost:8001`.

## Setup (once)

```bash
cd tests/e2e
npm install
npx playwright install chromium
```

## Run

```bash
cd tests/e2e
npm test              # headless
npm run test:headed   # headed browser
npm run report        # open last HTML report
```

## Tests

- `navigation.spec.js` — dashboard screenshot + each of the 7 nav tabs loads
  with the expected URL and heading, plus an end-to-end walk-through.
