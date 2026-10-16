# CareSlot – Clinic Appointment System

CareSlot is a front-desk app for a small multi-doctor clinic. Reception staff use it to register patients, book them in with a doctor, check them in when they arrive and mark the visit done. The dashboard shows today's schedule, who is in the waiting room and how busy each doctor is.

**Presentation:** [Google Slides](https://docs.google.com/presentation/d/1gozq9zRrB_hWzUNHuiw40d-w5joAO3xT/edit?usp=sharing) · [PowerPoint file](demo/ppt/CareSlot_DevOps_Presentation.pptx) · [Screenshots](screenshots/README.md)


It's my final DevOps capstone: the app itself is small, and most of the work is in taking it from my laptop to a monitored Kubernetes cluster on AWS through a CI/CD pipeline.

**Stack:** React + Vite · FastAPI · PostgreSQL · SQLAlchemy + Alembic · Pytest · Docker · GitHub Actions · Trivy · GHCR · Terraform (AWS VPC + EKS) · Helm · ingress-nginx · HPA · Prometheus + Grafana

---

## Architecture

```
 developer ── git push ──► GitHub ──► GitHub Actions
                                         │
                       ┌─────────────────┼──────────────────────┐
                       │ test            │ build                │ deploy
                       │  pytest         │  docker build x2     │  aws (OIDC role)
                       │  npm run build  │  trivy scan          │  helm upgrade --install
                       │                 │  push ghcr.io :sha   │
                       └─────────────────┴──────────┬───────────┘
                                                    ▼
          Terraform ──► AWS ap-south-1:  VPC (2 public + 2 private subnets, NAT)
                                          └── EKS cluster + managed node group
                                                    │
                       ingress-nginx (NLB) ─────────┤
                         /      → frontend (2 pods, nginx + React build)
                         /api   → backend  (2-6 pods, FastAPI, HPA on CPU)
                                              │
                                              └──► PostgreSQL (StatefulSet + gp3 PVC)

          Prometheus ── scrapes /metrics via ServiceMonitor ──► Grafana dashboard
```

## Repository layout

```
├── backend/                FastAPI app
│   ├── app/                routers, models, schemas, db config
│   ├── alembic/            migrations
│   ├── tests/              pytest suite (sqlite, never touches postgres)
│   └── Dockerfile
├── frontend/               React + Vite app, nginx config, Dockerfile
├── docker-compose.yml      full local stack
├── .github/workflows/      CI/CD pipeline
├── terraform/              AWS VPC + EKS + GitHub OIDC role
├── helm/careslot/          Helm chart for the whole app
├── k8s/                    namespace + storage class
├── monitoring/             prometheus/grafana + ingress-nginx values, dashboard
├── troubleshooting/        broken manifests for the failure demo
├── scripts/                cluster add-on install, load test
└── docs/                   trivy notes, demo script
```

---

## The application

### Features
- Dashboard: appointments today, waiting room, completed/cancelled counts, busiest doctor, today's timeline with one-click check-in / done
- Appointments: filter by day, doctor and status; change status inline; book new appointments
- Patients: search by name or phone, add, edit, delete
- Doctors: add, mark on/off duty, remove
- Booking rules enforced by the API: no double-booking a doctor, no bookings for off-duty doctors, phone numbers unique
- Priority (routine / urgent) on every appointment, with a badge and a filter
- Recent activity feed: bookings, check-ins, new patients and doctor changes
- Sidebar build indicator: API/database status plus the git SHA and environment that's currently deployed, so after a pipeline run you can see the new version is live

### API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | liveness, process is up |
| GET | `/ready` | readiness, also checks the database |
| GET | `/metrics` | Prometheus metrics |
| GET/POST | `/api/doctors` | list (`?active_only=true`) / create |
| GET/PUT/DELETE | `/api/doctors/{id}` | read / update / delete |
| GET/POST | `/api/patients` | list (`?q=search`) / create |
| GET/PUT/DELETE | `/api/patients/{id}` | read / update / delete |
| GET/POST | `/api/appointments` | list (`?day=YYYY-MM-DD&doctor_id=&status_filter=&priority=`) / book |
| GET/PUT/DELETE | `/api/appointments/{id}` | read / update (incl. status) / delete |
| GET | `/api/stats` | numbers for the dashboard |
| GET | `/api/activity` | recent activity feed (`?limit=10`) |
| GET | `/api/info` | deployed version, environment and database status |

Interactive docs: `http://localhost:8000/docs`

Times are stored in UTC; "today" is worked out in the clinic's timezone (`CLINIC_TZ`, default `Asia/Kolkata`).

---

## Running locally

### Docker Compose (everything)

```bash
docker compose up --build
```

- App: http://localhost:3000
- API docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

The backend runs `alembic upgrade head` on start and, with `SEED_DATA=true`, adds a few doctors, patients and today's appointments so the dashboard isn't empty.

If a port is already taken: `BACKEND_PORT=8001 FRONTEND_PORT=3001 docker compose up --build`

Stop with `docker compose down` (add `-v` to wipe the database).

### Backend on its own

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

export DATABASE_URL=postgresql+psycopg://careslot:careslot@localhost:5432/careslot
alembic upgrade head
python -m app.seed               # optional demo data
uvicorn app.main:app --reload --port 8000
```

### Frontend on its own

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173, /api is proxied to :8000
```

---

## Tests

```bash
cd backend
pytest -v
```

26 tests across health/ready/metrics/info, doctors, patients, appointments (including double booking, cancelled-slot rebooking, priority and stats) and the activity feed. `tests/conftest.py` sets `DATABASE_URL=sqlite://` and overrides the `get_db` dependency with an in-memory SQLite session, so tests never touch a real database and every test starts from empty tables.

In CI, a failing test stops the pipeline before any image is built.

---

## Docker

| Image | Base | Notes |
|---|---|---|
| `backend` | `python:3.12-slim` | runs as uid 10001, pip removed after install, migrations on start, healthcheck on `/health` |
| `frontend` | `node:22-alpine` → `nginx-unprivileged:alpine` | multi-stage: Node only builds `dist/`, runtime is nginx as uid 101 on port 8080, proxies `/api` to the backend |

```bash
docker build -t careslot-backend:local ./backend
docker build -t careslot-frontend:local ./frontend
```

---

## CI/CD – `.github/workflows/ci-cd.yml`

Runs on every push and pull request to `main`.

1. **test**: install deps, `pytest -v --cov`, then `npm ci && npm run build`
2. **build** (matrix: backend, frontend): build the image, **Trivy scan** (fails on HIGH/CRITICAL with a fix available), push to `ghcr.io/yashukiran/careslot-<service>:<commit-sha>`
3. **deploy**: only on `main`, and only once the `AWS_ROLE_ARN` repo variable exists. Logs in to AWS through GitHub OIDC (no AWS keys stored in GitHub), then `helm upgrade --install` with the new SHA tag and waits for the rollout.

Images are tagged with the commit SHA, never `latest`, so any running pod can be traced back to the exact commit that built it.

PRs run test + build + scan but don't push or deploy.

Trivy notes are in [`docs/trivy.md`](docs/trivy.md).

---

## Terraform – AWS infrastructure

`terraform/` creates, in `ap-south-1`:

- VPC `10.20.0.0/16` with **2 public** and **2 private** subnets across 2 AZs, internet gateway, one NAT gateway
- **EKS** cluster (`careslot-eks`) with a managed node group (2× t3.medium, scales 1–3) in the private subnets
- EKS add-ons: vpc-cni, coredns, kube-proxy, pod identity agent, **metrics-server** (for HPA), **EBS CSI driver** (for the postgres volume)
- GitHub OIDC provider + IAM role that only `main` of this repo can assume, mapped to the cluster with an EKS access entry

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # optional, defaults work
terraform init
terraform plan
terraform apply                                  # ~15 min

aws eks update-kubeconfig --region ap-south-1 --name careslot-eks
terraform output github_actions_role_arn         # → GitHub repo variable AWS_ROLE_ARN
```

AWS credentials come from `aws configure`; nothing secret is in the repo (`*.tfvars` and state files are git-ignored).

**Cost:** EKS control plane + NAT + 2 nodes ≈ US$0.30/hour. Always tear down after the demo:

```bash
helm uninstall careslot -n careslot
helm uninstall ingress-nginx -n ingress-nginx    # removes the NLB so the VPC can be deleted
helm uninstall kube-prometheus-stack -n monitoring
terraform destroy
```

---

## Running the Kubernetes part locally (kind)

I don't have a paid AWS account, so for the demo the cluster runs on my laptop with [kind](https://kind.sigs.k8s.io/). The chart, ingress, HPA and monitoring are exactly the same as for EKS; only the cluster underneath changes.

```bash
./scripts/setup-local-cluster.sh
```

That creates the cluster from `k8s/kind-cluster.yaml`, installs metrics-server, ingress-nginx, kube-prometheus-stack and the Grafana dashboard, then deploys the chart using the GHCR image built for the current commit.

- App through the ingress: http://careslot.127.0.0.1.nip.io (nip.io resolves to 127.0.0.1, so no hosts-file changes)
- Prometheus: `kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090` → http://localhost:9090/targets
- Grafana: `kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3002:80` → http://localhost:3002 (admin / careslot-admin)

The **Deploy to local cluster** job in the pipeline runs on a self-hosted GitHub Actions runner on the same machine, so a push to `main` rolls the new image out to this cluster. It's switched on with the repository variable `LOCAL_DEPLOY=true`.

Delete everything with `kind delete cluster --name careslot`.

## Kubernetes + Helm

One-time cluster setup on EKS (storage class, monitoring stack, ingress controller, dashboard):

```bash
./scripts/install-addons.sh
```

Deploy the app (CI does this automatically on every push to main):

```bash
helm upgrade --install careslot ./helm/careslot \
  -n careslot --create-namespace \
  -f helm/careslot/values-dev.yaml \
  --set backend.image.tag=<sha> --set frontend.image.tag=<sha>
```

The chart (`helm/careslot`) contains:

| Template | What it does |
|---|---|
| `backend.yaml` | Deployment (2 replicas, startup/liveness/readiness probes on `/health` and `/ready`, waits for postgres), ClusterIP Service, HPA 2→6 pods at 60% CPU |
| `frontend.yaml` | Deployment (2 replicas) + ClusterIP Service |
| `postgres.yaml` | StatefulSet with a 2Gi PVC + Service |
| `secret.yaml` | DB credentials / `DATABASE_URL` |
| `ingress.yaml` | `/` → frontend, `/api` → backend (nginx ingress class) |
| `servicemonitor.yaml` | tells Prometheus to scrape the backend's `/metrics` |

```bash
kubectl get pods,svc,ingress,hpa -n careslot
helm list -n careslot
helm history careslot -n careslot
helm rollback careslot <revision> -n careslot
```

### Ingress vs ingress controller

The `Ingress` in the chart is only a set of routing rules (`/` → frontend, `/api` → backend). Nothing happens until an **ingress controller** reads those rules and actually proxies the traffic. Here that's ingress-nginx, installed separately (`scripts/install-addons.sh` on EKS, `scripts/setup-local-cluster.sh` locally). Without it the Ingress object exists but `ADDRESS` stays empty.

### PostgreSQL in the cluster vs Amazon RDS

For this project Postgres runs inside Kubernetes as a StatefulSet with a PersistentVolumeClaim. That keeps the whole stack in one Helm chart, costs nothing extra and works the same on kind and EKS, which is right for a classroom/demo environment.

For a real clinic I'd move the database to **Amazon RDS**:

| | Postgres StatefulSet (this project) | Amazon RDS |
|---|---|---|
| Backups / point-in-time restore | do it yourself (cron + `pg_dump`) | automatic |
| High availability | single pod, single volume in one AZ | Multi-AZ standby with automatic failover |
| Upgrades, patching | manual | managed maintenance windows |
| Cost | just the node + EBS volume | extra monthly cost |
| Portability | same chart anywhere | AWS only |

Patient data is the one thing the clinic can't lose, so losing a node shouldn't put it at risk. The app wouldn't change: only `DATABASE_URL` in the Secret would point to the RDS endpoint, and Terraform would create the RDS instance in the private subnets.

Open the app at the ingress load balancer address:

```bash
kubectl get svc ingress-nginx-controller -n ingress-nginx    # EXTERNAL-IP column
```

### Autoscaling demo

```bash
kubectl get hpa -n careslot -w          # in one terminal
./scripts/loadtest.sh                   # in another (runs a load generator pod)
```

---

## Monitoring

- `prometheus-fastapi-instrumentator` exposes `http_requests_total` and `http_request_duration_seconds` on `/metrics`
- kube-prometheus-stack runs Prometheus + Grafana; the chart's ServiceMonitor makes Prometheus scrape the backend
- `monitoring/grafana-dashboard.yaml` is loaded automatically by Grafana's sidecar: requests/sec, p95 latency, 5xx rate, backend pod count, requests and latency per endpoint, CPU per pod

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
# http://localhost:9090/targets  → serviceMonitor/careslot/careslot-backend should be UP

kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3002:80
# http://localhost:3002  (admin / careslot-admin) → Dashboards → CareSlot API
```

---

## Troubleshooting lab

[`troubleshooting/README.md`](troubleshooting/README.md) walks through two broken manifests:

1. `broken-image.yaml`: wrong image tag → `ImagePullBackOff`
2. `broken-service.yaml`: selector doesn't match pod labels → Service with no endpoints

---

## Demo

The step-by-step presentation flow is in [`docs/demo.md`](docs/demo.md).
