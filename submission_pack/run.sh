#!/usr/bin/env bash
set -euo pipefail

T0="${1:?FATAL: no timestamp argument supplied by platform}"
echo "[run] t0=${T0} submission=${SUBMISSION_ID:-unknown}"

OUT=/tmp/forecast.json

# ================= EDIT THIS LINE =============================
# Run whatever produces your forecast. It must write JSON to $OUT.
#   python3 /app/model.py "$T0" > "$OUT"
#   Rscript /app/model.R "$T0" "$OUT"
#   /app/my_binary --t0 "$T0" --out "$OUT"
python3 /app/model.py "$T0" > "$OUT"
# ==============================================================

echo "[run] produced $(wc -c < "$OUT") bytes"
/app/upload.sh "$OUT"
echo "[run] done"
