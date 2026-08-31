# Bettercatan

Random Catan board generator with containerized runtime and automated vulnerability scanning.

## Quick start

```bash
# Local Python
pip install -r requirements.txt
python catan/catan_randomizer.py

# Docker
docker build -t bettercatan .
docker run --rm -v "%cd%\output:/app/output" bettercatan --mode 34 --output /app/output/catan_board.png --no-open

# Makefile (Linux/macOS/WSL/Git Bash)
make build
make run MODE=56
make scan
```

## Security tooling

This repo includes a small DevSecOps setup that is useful to discuss in interviews:

| Control | What it does |
|--------|----------------|
| Multi-stage Dockerfile | Keeps build tools out of the runtime image |
| Non-root user | Container runs as UID 10001 |
| Pinned dependencies | `requirements.txt` uses exact versions |
| Trivy image scan | Finds OS/package CVEs in the built image |
| Trivy config scan | Checks Dockerfile and IaC for misconfigurations |
| Trivy secret scan | Detects accidentally copied credentials |
| SBOM generation | `make scan-sbom` emits SPDX JSON |
| GitHub Actions | Builds image and uploads SARIF on every PR |

### Scan commands

```bash
make scan          # image vulnerabilities + misconfig + secrets
make scan-config   # Dockerfile/repo config only
make scan-deps     # Python dependency CVEs on the host tree
make scan-sbom     # write output/sbom.spdx.json
make lint-dockerfile
```

Trivy runs via its official container image, so you do not need a local Trivy install.

### Interview talking points

1. **Shift left**: dependency pinning + CI scanning before deploy.
2. **Defense in depth**: non-root runtime, minimal base image, `.dockerignore` to avoid leaking secrets.
3. **Supply chain**: SBOM generation and CVE triage with `.trivyignore` (document every exception).
4. **Observability of risk**: SARIF upload integrates with GitHub Security tab.
5. **Fail closed**: CI exits non-zero on CRITICAL image findings.

## Windows notes

- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- `make` is optional; run the equivalent `docker` commands directly, or install Make via WSL or Chocolatey.
- For interactive mode inside Docker: `docker run --rm -it bettercatan --interactive`.
