# 📡 WifiPlan — Browser-Based Wireless Network Planner

A production-oriented MVP for enterprise Wi-Fi AP planning with:
- Floor plan upload and AI-assisted wall detection (classical CV + ML stub)
- Interactive 2D canvas planner (pan/zoom, draw walls, place APs)
- Simplified RF heatmap simulation (log-distance path loss + wall attenuation)
- 3D floor extrusion view (React Three Fiber)
- Async job system (Celery + Redis)
- Multi-tenant SaaS architecture (JWT auth, org scoping)
- AP catalog with 8 vendors × 2 models each (demo seed data)

---

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env          # review defaults, no changes needed locally

# 2. Start all services
make up
# or: docker compose up -d --build

# 3. Wait ~15s for Postgres to initialize, then run migrations
make migrate                  # runs: alembic upgrade head

# 4. Seed demo data
make seed                     # creates demo user + AP catalog

# 5. Open the app
open http://localhost:3000

# Demo credentials:
#   Email:    admin@demo.com
#   Password: Demo1234!
```

The frontend requires Node.js 22 or newer (`frontend/.nvmrc` selects Node 22).
Floor-plan uploads support PNG, JPG,
PDF, and DXF. DWG is not accepted until an ODA File Converter is included and
validated in the worker image.

**Services started:**

| Service  | URL                          | Notes                    |
|----------|------------------------------|--------------------------|
| Frontend | http://localhost:3000        | Next.js 16               |
| API      | http://localhost:8000/docs   | FastAPI + Swagger UI     |
| MinIO    | http://localhost:9001        | minioadmin / minioadmin  |
| Postgres | localhost:5432               | wifiplan / wifiplan      |
| Redis    | localhost:6379               | job broker               |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Next.js 16 (App Router)                                  │  │
│  │  ├── Auth pages (login / register)                        │  │
│  │  ├── Dashboard (projects list)                            │  │
│  │  └── Planner (/projects/[id]/floors/[id]/planner)        │  │
│  │       ├── PlannerCanvas2D  ← HTML5 Canvas (pan/zoom/draw) │  │
│  │       ├── PlannerView3D    ← React Three Fiber            │  │
│  │       ├── PlannerToolbar   ← tool selection               │  │
│  │       ├── PlannerSidebar   ← AP catalog                   │  │
│  │       └── InspectorPanel   ← selected object props        │  │
│  │  State: Zustand stores (auth, planner)                    │  │
│  │  Data:  TanStack Query → axios → FastAPI                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │ HTTP/REST (JWT Bearer)
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (Python 3.11)                                           │
│  ├── /api/v1/auth/*          JWT register / login / refresh     │
│  ├── /api/v1/orgs/{id}/projects/*   project + building + floor  │
│  ├── /api/v1/floors/{id}/upload     floor plan ingestion        │
│  ├── /api/v1/floors/{id}/geometry/* walls / openings / obstacles│
│  ├── /api/v1/floors/{id}/aps/*      AP placement CRUD           │
│  ├── /api/v1/floors/{id}/rf/*       RF simulation trigger       │
│  ├── /api/v1/catalog/*              AP vendor + model catalog   │
│  ├── /api/v1/jobs/{id}              job status polling          │
│  └── /api/v1/orgs/{id}/projects/{id}/report/json                │
└─────────────────────────────────────────────────────────────────┘
           │ Celery tasks (Redis broker)
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Celery Worker                                                   │
│  ├── cv_pipeline queue                                           │
│  │   └── analyze_floor_plan(job_id, asset_id)                   │
│  │       → download S3 → run_pipeline() → save geometry to DB   │
│  └── rf_engine queue                                             │
│      └── run_rf_simulation(job_id, floor_id, band, grid_res)    │
│          → load geometry + APs → compute_heatmap() → S3 PNG     │
└─────────────────────────────────────────────────────────────────┘
           │                    │
           ▼                    ▼
    PostgreSQL 15          MinIO (S3)
    (all entities)         (floor plan images, heatmap PNGs)
```

---

## Project Structure

```
wifiplan/
├── .env.example
├── docker-compose.yml
├── Makefile
│
├── backend/
│   ├── app/
│   │   ├── main.py               FastAPI app entry point
│   │   ├── core/
│   │   │   ├── config.py         Pydantic settings (env-driven)
│   │   │   └── security.py       JWT + bcrypt
│   │   ├── db/base.py            SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── tenant.py         Organization, User, Membership
│   │   │   ├── project.py        Project, Building, Floor, FloorPlanAsset
│   │   │   ├── geometry.py       Wall, Opening, Obstacle, ScopeZone
│   │   │   ├── ap.py             APVendor, APModel, PlacedAP
│   │   │   └── jobs.py           Job, RFSimulationRun
│   │   ├── schemas/              Pydantic request/response DTOs
│   │   ├── api/v1/endpoints/     Route handlers
│   │   ├── services/
│   │   │   ├── rf_engine.py      RF propagation model
│   │   │   └── storage.py        S3-compatible storage abstraction
│   │   ├── cv/
│   │   │   └── pipeline.py       Floor plan CV analysis pipeline
│   │   ├── workers/
│   │   │   ├── celery_app.py     Celery configuration
│   │   │   └── tasks.py          Async task implementations
│   │   └── seeds/
│   │       ├── ap_catalog.py     AP vendor/model seed data
│   │       └── run.py            Seed runner script
│   ├── alembic/                  DB migrations
│   └── tests/                   pytest test suite
│
└── frontend/
    ├── app/                      Next.js App Router pages
    │   ├── auth/login/           Login page
    │   ├── auth/register/        Register page
    │   ├── dashboard/            Project list
    │   └── projects/[id]/floors/[id]/planner/  Main planner
    ├── components/
    │   ├── canvas/PlannerCanvas2D.tsx  HTML5 Canvas 2D planner
    │   ├── three/PlannerView3D.tsx     React Three Fiber 3D view
    │   └── planner/              Toolbar, sidebar, inspector, topbar
    ├── store/
    │   ├── auth.ts               Zustand auth store
    │   └── planner.ts            Zustand planner state
    ├── lib/api.ts                Axios client with JWT refresh
    ├── hooks/useJobPolling.ts    Job status polling hook
    └── types/index.ts            TypeScript domain types
```

---

## RF Engine

**MVP implementation** (`backend/app/services/rf_engine.py`):

- Log-distance path loss based on ITU indoor model
- Per-band parameters (2.4 / 5 / 6 GHz) with different path loss exponents
- Ray-cast wall intersection → accumulate attenuation in dB
- Material-based attenuation lookup table (glass → concrete → metal)
- Max-combining across APs (best signal wins per cell)
- Output: RSSI grid as numpy array + RGBA PNG for overlay rendering

**Coverage thresholds:**
- Good: ≥ −65 dBm
- Fair: −65 to −75 dBm
- Poor: < −75 dBm

**Limitations (MVP):** No multipath, no diffraction, no 3D propagation, no channel interference, no beamforming. This is a directional indicator, not a calibrated survey tool.

---

## Floor Plan CV Pipeline

**MVP implementation** (`backend/app/cv/pipeline.py`):

1. **Preprocessing** — grayscale, adaptive threshold, Gaussian blur, Canny edges
2. **Line detection** — Hough Transform (HoughLinesP)
3. **Cleanup** — remove short segments, merge collinear, snap endpoints
4. **Material grouping** — line-thickness heuristic (dark pixel ratio in ROI)
5. **Scope detection** — largest external contour as perimeter polygon
6. **ML stub** — `_ml_inference_stub()` returns None unless `MODEL_INFERENCE_ENABLED=true`

Every detected geometry object carries `confidence` (0.0–1.0) and `is_accepted=False` — the user must accept/edit/reject in the planner UI.

**V2 upgrade:** Replace stub with HTTP call to model inference microservice.  
**Advanced:** Deploy fine-tuned segmentation model on GPU (TorchServe / Triton).

---

## Multi-Tenant Architecture

Single database with `organization_id` foreign key on all top-level entities.  
All API endpoints verify membership before querying. Roles: `admin / editor / viewer`.

Future stronger isolation: row-level security (PostgreSQL RLS), or separate schemas per tenant.

---

## Running Tests

```bash
# Unit tests (no services needed) — always runnable
make test-unit
# → 33 tests: RF engine physics + CV pipeline

# API integration tests (requires Postgres)
docker compose up postgres -d
sleep 10 && make migrate
make test-api
# → auth, projects, geometry CRUD
```

---

## Cloud Deployment Target

```
CDN (CloudFront) → Next.js (Vercel / ECS)
                → FastAPI (ECS Fargate)
                   → PostgreSQL (RDS)
                   → Redis (ElastiCache)
                   → Worker (ECS Fargate, auto-scaled)
                   → S3 (floor plans, heatmaps)
                   → Model inference (optional ECS GPU task)
```

---

## Known Limitations (MVP)

| Area | Limitation |
|------|-----------|
| RF model | Simplified log-distance, no calibration, no multipath |
| CV pipeline | Hough-based, struggles with low-contrast or hand-drawn plans |
| Material detection | Heuristic only — line darkness proxy |
| Scale calibration | Manual (set `scale_px_per_m` via PATCH /floors/{id}) |
| 3D view | Single-floor extrusion only |
| PDF floor plans | Not yet converted to raster in worker |
| Reports | JSON only — PDF generation scaffolded but not implemented |
| AP auto-placement | Manual only — auto-placement algorithm not yet built |
| Channel planning | Not implemented |

---

## Roadmap

- [ ] Scale calibration UI (click two known points)
- [ ] CV geometry review UI (accept/reject panel per detected element)
- [ ] PDF floor plan rasterization in worker (pdf2image / poppler)
- [ ] ML model inference integration (wall segmentation fine-tuned model)
- [ ] AP auto-placement algorithm (coverage optimization)
- [ ] Channel plan assignment (least-overlap greedy)
- [ ] Multi-floor stacking in 3D view
- [ ] PDF report generation (WeasyPrint or headless Chrome)
- [ ] Real-time collaboration (WebSocket presence)
- [ ] RBAC enforcement at viewer level
- [ ] Row-level security for enterprise tenant isolation
