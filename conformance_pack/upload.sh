#!/usr/bin/env bash
set -euo pipefail

FILE="${1:?usage: upload.sh <file>}"
: "${OUTPUT_POST:?FATAL: OUTPUT_POST not set by platform}"

URL=$(printf '%s' "$OUTPUT_POST" | jq -r '.url')

ARGS=()
while IFS=$'\t' read -r k v; do
  ARGS+=(-F "${k}=${v}")
done < <(printf '%s' "$OUTPUT_POST" | jq -r '.fields | to_entries[] | [.key, .value] | @tsv')

# 'file' MUST be the last form field — S3 ignores anything after it.
curl -fsS --retry 3 --retry-delay 2 --max-time 120 \
     -X POST "${ARGS[@]}" -F "file=@${FILE}" "$URL"

echo "[upload] ok"
