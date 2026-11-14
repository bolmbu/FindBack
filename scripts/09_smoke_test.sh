#!/usr/bin/env bash
set -euo pipefail
: "${API_URL:?API_URL is not set; run step API Gateway first}"
for path in items matches; do
  printf '%s HTTP ' "$path"
  curl --fail --silent --show-error -o "/tmp/findback-${path}.json" \
    -w '%{http_code}\n' "${API_URL}/${path}"
  python3 -m json.tool "/tmp/findback-${path}.json" >/dev/null
  printf '%s JSON OK\n' "$path"
done
