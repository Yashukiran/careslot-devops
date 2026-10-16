# Screenshots

Taken from the running project: the app and monitoring stack on a local kind Kubernetes cluster, CI/CD on GitHub Actions, images on GHCR. I don't have a paid AWS account, so the cluster for the demo is kind instead of EKS; the Terraform code for VPC + EKS is in `terraform/` and validates, but wasn't applied.

## M1 – Application

| | |
|---|---|
| Dashboard through the ingress (`careslot.127.0.0.1.nip.io`) | ![](03_frontend_dashboard.png) |
| Appointments with filters | ![](03_b_frontend_appointments.png) |
| Patients | ![](03_c_frontend_patients.png) |
| Doctors | ![](03_d_frontend_doctors.png) |
| FastAPI Swagger docs | ![](04_backend_api_docs.png) |

## M2 – Tests

![pytest](01_pytest_terminal.png)

## M3 – Git

![git log](06_git_log_commits.png)
![commits on GitHub](06_github_commits.png)

## M5 / M6 – CI/CD, Trivy, GHCR

The pipeline runs pytest, builds both images, scans them with Trivy (the job fails on HIGH/CRITICAL findings) and pushes them to GHCR tagged with the commit SHA. See [`docs/trivy.md`](../docs/trivy.md) for what the scan found and how it was fixed.

![pipeline](07_github_actions_pipeline.png)
![packages](08_a_packages.png)
![sha tags](08_b_package_sha_tags.png)

## M8 – Kubernetes + Helm

![cluster](11_kind_cluster_nodes.png)
![pods](14_kubectl_pods_running.png)
![svc + ingress](15_kubectl_svc_ingress.png)
![helm](16_helm_list.png)
![hpa](19_kubectl_hpa_autoscaling.png)

## M9 – Monitoring

![metrics](05_backend_metrics.png)
![prometheus targets](17_prometheus_targets.png)
![grafana](18_grafana_dashboard.png)

## Troubleshooting lab

![broken service](20_troubleshooting_broken_service.png)
![broken image](21_troubleshooting_broken_image.png)
