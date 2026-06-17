# Multi-Agent UI E2E Tests (Sprint 13)

Playwright browser tests for the 8-workstream multi-agent UI flows:
Agent Selection, Parallel Sessions, Interview Room tabs, and Ajan Yönetimi.

## Prerequisites

- API reachable at `http://localhost:8000/api/v1` (kubectl port-forward to `aakp-api` pod)
- Node.js 18+

```powershell
# Terminal 1 — API (skip if already running)
$pod = kubectl get pod -n aakp-information -l app=aakp-api -o jsonpath='{.items[0].metadata.name}'
kubectl port-forward -n aakp-information pod/$pod 8000:8000

# Terminal 2 — install + run
cd services/frontend
npm install
npx playwright install chromium
npm run test:e2e
```

Environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_BASE` | `http://localhost:8000/api/v1` | Fixture seed / global-setup healthcheck |
| `PLAYWRIGHT_BASE_URL` | `http://localhost:5173` (local) / `http://localhost:8088` (k8s) | Frontend base URL |

## Local (Vite dev server)

`playwright.config.ts` starts `npm run dev` automatically and runs with 4 workers.

```powershell
cd services/frontend
npm run test:e2e
```

Run a single spec:

```powershell
npx playwright test e2e/multi-agent/agent-selection.spec.ts
```

## K8s smoke

Port-forward the cluster frontend and API, then run the same suite against nginx:

```powershell
# Frontend (nginx)
kubectl port-forward -n aakp-information svc/aakp-frontend 8088:80

# API (if not already forwarded)
$pod = kubectl get pod -n aakp-information -l app=aakp-api -o jsonpath='{.items[0].metadata.name}'
kubectl port-forward -n aakp-information pod/$pod 8000:8000

cd services/frontend
$env:PLAYWRIGHT_BASE_URL = "http://localhost:8088"
npm run test:e2e:k8s
```

`playwright.k8s.config.ts` uses 2 workers and does **not** start a local web server.

## Structure

```
e2e/
  fixtures/api.ts       # assessment + task seed helpers
  pages/                # page objects
  multi-agent/          # spec files (one per screen)
  global-setup.ts       # API healthcheck
```

## Success criteria

- 4 spec files, ~12 tests, all passing locally against port-forwarded API
- K8s config smoke passes with frontend on `:8088` (port-forward `8088:80`) after S14 deploy updates cluster image
