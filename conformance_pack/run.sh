#!/usr/bin/env bash
set -euo pipefail

T0="${1:?FATAL: no timestamp argument supplied by platform}"
echo "[conformance] t0=${T0} submission=${SUBMISSION_ID:-unknown}"

# Egress check: reported, never fatal. A third-party outage must not tell a
# hundred teams their access is broken when it isn't.
CODE=$(curl -sS -o /dev/null -m 30 -w '%{http_code}' \
       https://services.swpc.noaa.gov/text/ace-swepam.txt 2>/dev/null || echo "failed")
echo "[conformance] egress check -> ${CODE}"

OUT=/tmp/forecast.json
jq -n --arg t0 "$T0" '{t0: $t0, forecast_speed_kms: [range(72) | 420.0]}' > "$OUT"

echo "[conformance] produced $(wc -c < "$OUT") bytes"
/app/upload.sh "$OUT"
echo "[conformance] PASS"
