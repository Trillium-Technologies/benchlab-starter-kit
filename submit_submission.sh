#!/usr/bin/env bash
# Real submission upload: check your submission folder, zip it, fetch your
# upload form from the portal, and upload it.
#
#   bash submit_submission.sh           # check, zip, upload submission_pack/
#   bash submit_submission.sh status    # show your status, latest run and log links
#
# Uses the same .team file as submit_conformance.sh. Create it with:
#   cp .team.example .team     (then put your portal link in it)
#
# To upload a folder other than submission_pack/:
#   SUBMISSION_DIR=my_model bash submit_submission.sh
#
# Run local_tests/test_local.sh before every upload. This script only checks
# the zip's layout; it does not build or run your container.
#
# Needs: bash, curl, jq, zip.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

die() { echo "ERROR: $*" >&2; exit 1; }

SUBMISSION_DIR="${SUBMISSION_DIR:-submission_pack}"
ZIP=submission.zip
MAX_ZIP_BYTES=$((500 * 1024 * 1024))

for tool in curl jq zip; do
  command -v "$tool" >/dev/null 2>&1 || die "'$tool' is not installed"
done

[ -f .team ] || die ".team not found. Run: cp .team.example .team   and put your portal link in it."
# shellcheck disable=SC1091
source ./.team
case "${PORTAL:-}" in
  http*) ;;
  *) die "PORTAL in .team is empty or is not a link. Paste the full link from your email, inside the quotes." ;;
esac

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fetch_portal() {
  curl -fsS "$PORTAL" > "$TMP/portal.json" \
    || die "could not get your page from the portal. A 403 means the PORTAL link in .team is wrong or cut off."
  jq -e . "$TMP/portal.json" >/dev/null 2>&1 || die "the portal did not return JSON."
}

show_status() {
  jq '{submission_id, phase, accepting, eligibility, failure_reason,
       cpu_requested, cpu_granted, memory_requested, memory_granted}' "$TMP/portal.json"
  echo "Latest run (your dry run, until live cycles start):"
  jq '.recent_runs[0] // "none yet"
      | if type == "object" then {cycle_ts, status, failure_reason, exit_code, pull_seconds, run_seconds} else . end' \
    "$TMP/portal.json"
  echo "Log links (valid for 1 hour; build logs are gzipped, so pipe them through gunzip):"
  jq -r '.logs[]? | "\(.key)\n  \(.url)"' "$TMP/portal.json"
}

# Prints the FROM images that come from Docker Hub: no registry host in the
# name (e.g. ubuntu:22.04, rocker/r-ver), or docker.io itself. Skips --flags
# and references to earlier build stages (FROM x AS name ... FROM name).
docker_hub_images() {
  awk '
    toupper($1) == "FROM" {
      i = 2; while ($i ~ /^--/) i++
      img = $i
      if (toupper($(i + 1)) == "AS") stages[tolower($(i + 2))] = 1
      if (tolower(img) in stages || img == "scratch") next
      split(img, part, "/")
      if (part[1] == "docker.io" || index(img, "/") == 0 ||
          (part[1] !~ /[.:]/ && part[1] != "localhost")) printf "%s ", img
    }' "$1" | sed 's/ $//'
}

submit() {
  echo "1/5 Checking the portal is accepting real submissions..."
  fetch_portal
  PHASE=$(jq -r '.phase // empty' "$TMP/portal.json")
  case "$PHASE" in
    conformance) die "submissions are not open yet; the portal only accepts the conformance kit. Uploading now would mark your conformance as FAILED." ;;
    closed)      die "submissions are closed. Your last ELIGIBLE submission is the one that runs." ;;
  esac

  echo "2/5 Checking $SUBMISSION_DIR/..."
  [ -d "$SUBMISSION_DIR" ] || die "folder '$SUBMISSION_DIR' not found."
  for f in Dockerfile README.md submission.json; do
    [ -f "$SUBMISSION_DIR/$f" ] || die "$SUBMISSION_DIR/$f is missing. Dockerfile, README.md and submission.json are all required."
  done
  jq -e . "$SUBMISSION_DIR/submission.json" >/dev/null 2>&1 \
    || die "$SUBMISSION_DIR/submission.json is not valid JSON."
  HUB=$(docker_hub_images "$SUBMISSION_DIR/Dockerfile")
  if [ -n "$HUB" ]; then
    echo "WARNING: your Dockerfile pulls from Docker Hub ($HUB), which can fail with" >&2
    echo "         '429 Too Many Requests' on our build servers. Use the public.ecr.aws mirror" >&2
    echo "         (search gallery.ecr.aws). Continuing anyway." >&2
  fi

  echo "3/5 Zipping the contents of $SUBMISSION_DIR/ (not the folder itself)..."
  rm -f "$ZIP"
  (cd "$SUBMISSION_DIR" && zip -qr "../$ZIP" . -x 'local_tests/out/*' '*.DS_Store' '.git/*' '*__pycache__*')
  SIZE=$(wc -c < "$ZIP" | tr -d ' ')
  [ "$SIZE" -le "$MAX_ZIP_BYTES" ] \
    || die "$ZIP is $((SIZE / 1024 / 1024)) MB; the limit is 500 MB. Download large weights in your Dockerfile instead."
  echo "    $ZIP is $((SIZE / 1024)) KB (limit 500 MB)"

  echo "4/5 Getting your upload form from the portal..."
  URL=$(jq -r '.upload.url // empty' "$TMP/portal.json")
  [ -n "$URL" ] || die "the portal did not return an upload form."
  ARGS=()
  while IFS=$'\t' read -r k v; do
    ARGS+=(--form-string "$k=$v")
  done < <(jq -r '.upload.fields | to_entries[] | [.key, .value] | @tsv' "$TMP/portal.json")
  [ "${#ARGS[@]}" -gt 0 ] || die "the upload form had no fields."

  echo "5/5 Uploading $ZIP..."
  # 'file' must be the last form field: S3 ignores anything after it.
  CODE=$(curl -sS -o "$TMP/resp.txt" -w '%{http_code}' "${ARGS[@]}" -F "file=@$ZIP" "$URL") \
    || die "the upload request failed (network problem?)."

  if [ "$CODE" = "204" ]; then
    echo "HTTP status: 204. Your zip arrived, and it replaces any earlier submission."
    echo "Building and the dry run take a while. Then run:  bash submit_submission.sh status"
  else
    echo "HTTP status: $CODE. The upload was rejected:" >&2
    cat "$TMP/resp.txt" >&2
    echo >&2
    die "your upload form lasts 1 hour, so just run this script again."
  fi
}

case "${1:-submit}" in
  submit) submit ;;
  status) fetch_portal; show_status ;;
  *) die "usage: bash submit_submission.sh [status]" ;;
esac
