# Person C — TRANA Command Dashboard

## Local run (PowerShell)

```powershell
cd web/dashboard
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open http://localhost:5174. The dashboard joins once with COORD-01 and retains its session tab-locally. It reads event-derived camp/road/depots state, plan, tasks, insights and SSE. Plan approval is human-in-the-loop and handles 409 stale-plan responses. Mark-delivered actions are sent through POST /api/sync.

## Build/test

```powershell
npm run build
npm test
```

## Maps

MapLibre and PMTiles are registered. Configure VITE_OFFLINE_STYLE_URL with a local style JSON backed by a PMTiles archive. Without a local pack, the map remains a local canvas with the fictional scenario roads and camp markers; it does not call cloud tile services.

All numbers and scenario entities are simulated. Vehicles are informational only and are not capacity-planned.
