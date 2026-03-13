#!/usr/bin/env bash
set -euo pipefail

IMAGES=(
  "ghcr.io/glpi-project/glpi:10.0.16"
  "ghcr.io/glpi-project/glpi:10.0.17"
)

for image in "${IMAGES[@]}"; do
  echo "[glpikit] Running integration suite for ${image}"
  GLPI_IMAGE="${image}" docker compose -f docker/compose.glpi.yml up -d

  # Wait basic availability (customize endpoint for your environment)
  for _ in {1..30}; do
    if curl -fsS "http://localhost:8080" >/dev/null 2>&1; then
      break
    fi
    sleep 5
  done

  python -m pytest -q tests/integration || {
    echo "[glpikit] Integration failed for ${image}"
    GLPI_IMAGE="${image}" docker compose -f docker/compose.glpi.yml down -v
    exit 1
  }

  GLPI_IMAGE="${image}" docker compose -f docker/compose.glpi.yml down -v
  echo "[glpikit] Integration passed for ${image}"
done

echo "[glpikit] Integration matrix completed"
