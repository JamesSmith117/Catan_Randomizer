# Bettercatan — build, run, and security-scan helpers
#
# Requires: Docker (and optionally Make on Windows via WSL, Git Bash, or `choco install make`)
#
# Override defaults:
#   make IMAGE=bettercatan:dev scan

IMAGE       ?= bettercatan:latest
CONTAINER   ?= bettercatan-run
OUTPUT_DIR  ?= output
MODE        ?= 34
TRIVY_SEVERITY ?= HIGH,CRITICAL
TRIVY_IMAGE ?= aquasec/trivy:latest

.PHONY: help build run run-interactive shell clean scan scan-config scan-sbom scan-deps lint-dockerfile

help:
	@echo "Targets:"
	@echo "  build           Build the container image"
	@echo "  run             Generate a board (non-interactive, writes to ./$(OUTPUT_DIR))"
	@echo "  run-interactive Prompt for player count (requires TTY)"
	@echo "  shell           Open a shell in the runtime container"
	@echo "  scan            Scan the built image with Trivy (vulnerabilities + misconfigurations)"
	@echo "  scan-config     Scan the Dockerfile for misconfigurations"
	@echo "  scan-sbom       Generate an SPDX SBOM for the image"
	@echo "  scan-deps       Scan Python dependencies on the host filesystem"
	@echo "  lint-dockerfile Run Hadolint against the Dockerfile"
	@echo "  clean           Remove local image and output artifacts"

build:
	docker build -t $(IMAGE) .

run: build
	@mkdir -p $(OUTPUT_DIR)
	docker run --rm \
		-v "$(CURDIR)/$(OUTPUT_DIR):/app/output" \
		$(IMAGE) --mode $(MODE) --output /app/output/catan_board.png --no-open
	@echo "Board written to $(OUTPUT_DIR)/catan_board.png"

run-interactive: build
	docker run --rm -it $(IMAGE) --interactive

shell: build
	docker run --rm -it --entrypoint /bin/bash $(IMAGE)

scan: build
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v "$(CURDIR):/repo" \
		-w /repo \
		$(TRIVY_IMAGE) image \
			--severity $(TRIVY_SEVERITY) \
			--ignore-unfixed \
			--scanners vuln,misconfig,secret \
			$(IMAGE)

scan-config:
	docker run --rm \
		-v "$(CURDIR):/repo" \
		-w /repo \
		$(TRIVY_IMAGE) config \
			--severity $(TRIVY_SEVERITY) \
			.

scan-sbom: build
	@mkdir -p $(OUTPUT_DIR)
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v "$(CURDIR)/$(OUTPUT_DIR):/out" \
		$(TRIVY_IMAGE) image \
			--format spdx-json \
			-o /out/sbom.spdx.json \
			$(IMAGE)
	@echo "SBOM written to $(OUTPUT_DIR)/sbom.spdx.json"

scan-deps:
	docker run --rm \
		-v "$(CURDIR):/repo" \
		-w /repo \
		$(TRIVY_IMAGE) fs \
			--severity $(TRIVY_SEVERITY) \
			--scanners vuln \
			--skip-dirs .git,output \
			.

lint-dockerfile:
	docker run --rm -i hadolint/hadolint < Dockerfile

clean:
	-docker rmi $(IMAGE)
	-rm -rf $(OUTPUT_DIR)
