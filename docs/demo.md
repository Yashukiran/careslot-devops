# Demo script

Order for the final presentation. The cluster runs locally on kind (see the README), so before starting:

```bash
./scripts/setup-local-cluster.sh                     # cluster + monitoring + app (skip if already up)
# terminal 2 - keep open
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
# terminal 3 - keep open
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3002:80
# terminal 4 - the self-hosted GitHub runner
cd C:\actions-runner; .\run.cmd
```

Use `kubectl config use-context kind-careslot` so the commands below hit the right cluster.

## 1. Application
- Open http://careslot.127.0.0.1.nip.io (this goes through the ingress).
- Dashboard → **+ Book** → book an appointment → **Check in** → **Done**.
- Try booking the same doctor at an overlapping time → "Doctor already has an appointment in this time slot".

## 2. API
```bash
kubectl port-forward svc/careslot-backend 8000:8000 -n careslot
```
Open http://localhost:8000/docs and create / read / update / delete a doctor from Swagger. Show `/health`, `/ready` and `/metrics`.

## 3. Database
```bash
kubectl exec -it careslot-postgres-0 -n careslot -- psql -U careslot -d careslot \
  -c "select id, start_time, status, reason from appointments order by start_time;"
kubectl exec -it careslot-postgres-0 -n careslot -- psql -U careslot -d careslot -c "select * from alembic_version;"
```

## 4. Tests
```bash
cd backend && pytest -v
```

## 5. Git + CI + deploy (live change)
- Make a small visible change, e.g. the clinic name in `frontend/src/components/Sidebar.jsx`.
- `git commit -am "Rename clinic in sidebar" && git push`
- Actions tab: **Test → Build, scan & push (backend / frontend) → Deploy to local cluster**.
- `kubectl get pods -n careslot -w` shows the rolling update; refresh the app and the change is there.
- `kubectl describe deploy careslot-frontend -n careslot | grep Image` → tag = the commit SHA just pushed.

## 6. Docker + Trivy + GHCR
- Both Dockerfiles: multi-stage frontend, non-root users (`docker compose exec backend id`).
- Open the **Trivy scan** step log in the run and explain the result (`docs/trivy.md`).
- GitHub profile → Packages → `careslot-backend` / `careslot-frontend` with SHA tags.

## 7. Terraform
- Walk through `vpc.tf` (VPC, 2 public + 2 private subnets, NAT), `eks.tf` (cluster, node group, add-ons) and `github-oidc.tf`.
- `terraform init` and `terraform validate`.
- Explain that applying it needs a paid AWS account (EKS isn't in the free plan), which is why the cluster for the demo runs on kind, and that the same Helm chart deploys to both.

## 8. Kubernetes + Helm
```bash
kubectl apply -f k8s/namespace.yaml
kubectl get pods -n careslot -o wide
kubectl get svc,ingress -n careslot
helm list -n careslot
helm history careslot -n careslot
```

## 9. HPA
```bash
kubectl get hpa -n careslot -w        # one terminal
./scripts/loadtest.sh                 # another one
```
Replicas go 2 → 6 as CPU passes 60%, and drop back a few minutes after the load stops.

## 10. Monitoring
- http://localhost:9090/targets → `serviceMonitor/careslot/careslot-backend` is **UP**.
- http://localhost:3002 (admin / careslot-admin) → Dashboards → **CareSlot API** while the load test runs.

## 11. Troubleshooting
- `kubectl apply -f troubleshooting/broken-service.yaml`, show the empty endpoints, fix the selector live (see `troubleshooting/README.md`).
- `kubectl apply -f troubleshooting/broken-image.yaml` → `ImagePullBackOff` → `kubectl describe` → fix the tag.

## 12. Clean up
```bash
kind delete cluster --name careslot
```
