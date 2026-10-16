# Demo script

Rough order for the final presentation. Before starting: cluster is up (`terraform apply` + `scripts/install-addons.sh`), at least one green pipeline run, and port-forwards for Prometheus/Grafana open in separate terminals.

## 1. Application
- Open the app through the ingress address, walk through dashboard → book an appointment → check the patient in → mark done.
- Try to double-book the same doctor at the same time → error from the API.

## 2. API
- `http://<ingress>/docs` doesn't exist (ingress only routes `/api` + `/`), so show Swagger locally with `docker compose up` or via `kubectl port-forward svc/careslot-backend 8000:8000 -n careslot` → http://localhost:8000/docs
- Create / read / update / delete a doctor from Swagger.

## 3. Database
```bash
kubectl exec -it careslot-postgres-0 -n careslot -- psql -U careslot -d careslot \
  -c "select id, start_time, status, reason from appointments order by start_time;"
kubectl exec -it careslot-postgres-0 -n careslot -- psql -U careslot -d careslot -c "select * from alembic_version;"
```

## 4. Git + CI (live change)
- Small visible change, e.g. the clinic name in `frontend/src/components/Sidebar.jsx`.
- `git commit -am "Rename clinic in sidebar" && git push`
- Show the Actions run: test → build/scan (both images) → deploy.

## 5. Docker + Trivy + GHCR
- Point at the two Dockerfiles (multi-stage frontend, non-root users).
- Open the Trivy step log in the run, explain the result (`docs/trivy.md`).
- GHCR packages page: both images tagged with the commit SHA.

## 6. Terraform
- Walk through `vpc.tf`, `eks.tf`, `github-oidc.tf`.
- `terraform plan` → "No changes" (infra matches the code).
- AWS console: VPC with its 4 subnets, EKS cluster + node group.

## 7. Kubernetes + Helm
```bash
kubectl get pods -n careslot -o wide
kubectl get svc,ingress -n careslot
helm list -n careslot
helm history careslot -n careslot
kubectl describe deploy careslot-backend -n careslot | grep Image   # = the commit sha just pushed
```
- Refresh the app → the change from step 4 is live.

## 8. HPA
```bash
kubectl get hpa -n careslot -w
./scripts/loadtest.sh          # second terminal
```
Replicas go from 2 up as CPU passes 60%, and come back down a couple of minutes after the load stops.

## 9. Monitoring
- Prometheus → Status → Targets → `careslot-backend` is UP.
- Grafana → CareSlot API dashboard: request rate and pod count jump during the load test.

## 10. Troubleshooting
- `kubectl apply -f troubleshooting/broken-service.yaml`, show the empty endpoints, fix the selector live (see `troubleshooting/README.md`).
- Same for `broken-image.yaml` if time allows.

## 11. Clean up (after evaluation)
```bash
helm uninstall careslot -n careslot
helm uninstall ingress-nginx -n ingress-nginx
helm uninstall kube-prometheus-stack -n monitoring
cd terraform && terraform destroy
```
