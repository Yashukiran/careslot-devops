# Trivy scan notes

## What gets scanned

Each push builds two images, `careslot-backend` and `careslot-frontend`, and runs `trivy image` on each before it is pushed to GHCR. Trivy reads the OS package database of the image (Debian for the backend, Alpine for the frontend) and the language packages inside it (the Python `site-packages` in the backend), and compares the versions against its vulnerability database.

The step uses:

```
--severity HIGH,CRITICAL   only these two levels count
--ignore-unfixed           skip CVEs that have no patched version yet (nothing we could do about them)
--exit-code 1              any remaining finding fails the job, so the image is never pushed
```

## What I found and fixed

The first local scan of the backend reported **4 HIGH** findings and no CRITICAL:

| Package | CVE / advisory | Problem |
|---|---|---|
| setuptools 70.3.0 | CVE-2025-47273 | path traversal in `PackageIndex` |
| urllib3 2.7.0 | CVE-2026-97687, CVE-2026-97689 | HTTPS proxy TLS override / unbounded memory in the chunk parser (DoS) |
| msgpack 1.1.2 | GHSA-6v7p-g79w-8964 | out-of-bounds read when an `Unpacker` is reused |

None of these were dependencies of my app. They came from **pip and ensurepip that ship with the `python:3.12-slim` base image** (pip vendors its own copies of urllib3 and msgpack). Take CVE-2025-47273 as an example: setuptools' package-index code could be tricked into writing files outside the target directory when downloading a package. It only matters when something runs setuptools to install packages, which never happens in the running container.

Since pip is only needed while building the image, the Dockerfile now uninstalls pip and deletes the bundled ensurepip wheels right after `pip install -r requirements.txt`. The next scan was clean for both images, and the image is a bit smaller too.

The frontend image (`nginx-unprivileged` on Alpine, with `apk upgrade` during the build) was clean from the first scan.

## What a clean result means

A clean scan means no **known, already-fixed** HIGH/CRITICAL CVEs in the packages Trivy can see at build time. It doesn't mean the app is secure: it says nothing about bugs in my own code, leaked secrets, or CVEs published after the image was built. That's why the pipeline re-scans every new image, and why other layers (dependency updates, secret scanning, non-root containers, least-privilege IAM) still matter.

## Where Trivy fits among the security layers

Container scanning is only one layer. The ones the course lists, and where this project stands on each:

| Layer | What it checks | In this project |
|---|---|---|
| **SAST** (static analysis) | my own source code for insecure patterns (SQL injection, unsafe eval...) before it runs | not automated yet; SQLAlchemy queries are parameterised and pydantic validates every request body. Next step would be Bandit or Semgrep in the test job |
| **Dependency scanning** | known CVEs in libraries I pull in (`requirements.txt`, `package-lock.json`) | covered for the backend because Trivy reads the installed `site-packages` inside the image; versions are pinned so a scan result is reproducible |
| **Secret scanning** | API keys, passwords or tokens committed to git | GitHub's built-in secret scanning on the public repo; `.gitignore` keeps `.env`, `*.tfvars` and Terraform state out; CI logs in to AWS with OIDC so there are no long-lived AWS keys to leak |
| **Container scanning** | OS packages and libraries inside the final image | **Trivy, on both images, every push, failing on HIGH/CRITICAL** |
| **Runtime security** | what the container actually does while running | non-root users (uid 10001 / 101), `allowPrivilegeEscalation: false`, resource limits, separate namespace, DB password in a Secret instead of the image |

No single layer catches everything: Trivy won't find a bug in my booking logic, and SAST won't find an old OpenSSL in the base image.
