# Person B — TRANA Field PWA

## Run locally (PowerShell)

```powershell
cd web/field
npm install
npm run dev
```

Open http://localhost:5173. Join once while online using CAMP-A1, CAMP-B1, VOL-01 or VOL-02 from the local backend settings. Reports and task actions are written to Dexie/IndexedDB before network sync. The outbox is sent in batches to POST /api/sync; event data is sent before referenced photo blobs.

## Build and test

```powershell
npm run build
npm test
```

## Offline map pack

MapLibre and the PMTiles protocol are included. Supply a local style JSON referencing a PMTiles archive via VITE_OFFLINE_STYLE_URL; place large map packs under public/maps (do not commit them). Without a map pack the local map is a neutral offline canvas and makes no cloud tile requests. Credit OpenStreetMap contributors for OSM-derived extracts.

All data is simulated; do not collect beneficiary names or individual records.
