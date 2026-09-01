#!/usr/bin/env bash
set -euo pipefail

# Runs your container exactly as the platform will: same argv, same env vars,
# same upload path. Writes to ./out/ instead of S3, then validates.
#
#   ./test_local.sh 20261111T060000Z

CPU=${CPU:-4}
MEM=${MEM:-16g}
T0=${1:-$(date -u +%Y%m%dT%H0000Z)}

mkdir -p out && rm -f out/forecast.json

docker build --platform linux/amd64 -t swp-local ..

SIZE=$(docker image inspect swp-local --format '{{.Size}}')
echo "image size : $((SIZE / 1024 / 1024)) MiB   (cap 15360 MiB)"
[ "$SIZE" -lt 16106127360 ] || { echo "FAIL: image over 15 GiB"; exit 1; }
echo "est. pull  : ~$((SIZE / 100000000))s of your 900s budget"

python3 mock_platform.py & MOCK=$!
trap 'kill $MOCK 2>/dev/null || true' EXIT
sleep 1

# Linux needs host-gateway; Docker Desktop resolves host.docker.internal already.
EXTRA=()
[ "$(uname)" = "Linux" ] && EXTRA=(--add-host=host.docker.internal:host-gateway)

START=$(date +%s)
docker run --rm \
  --cpus="$CPU" --memory="$MEM" \
  "${EXTRA[@]}" \
  -e SUBMISSION_ID=sub_local \
  -e INFERENCE_TIMESTAMP="$T0" \
  -e OUTPUT_POST='{"url":"http://host.docker.internal:8899/","fields":{"key":"local"}}' \
  swp-local "$T0"
echo "runtime    : $(( $(date +%s) - START ))s   (cap 900s INCLUDING pull)"

[ -f out/forecast.json ] || { echo "FAIL: nothing uploaded"; exit 1; }
jq -e '.forecast_speed_kms | length == 72' out/forecast.json > /dev/null \
  || { echo "FAIL: not 72 values"; exit 1; }
jq -e '[.forecast_speed_kms[] | select(. != null and (isnan | not))] | all(. >= 0 and . <= 10000)' \
  out/forecast.json > /dev/null \
  || { echo "FAIL: value outside 0-10000 km/s"; exit 1; }

echo "PASS — out/forecast.json is valid"
