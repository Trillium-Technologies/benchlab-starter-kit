#!/usr/bin/env bash
# Prints this kit's manifest digest and compares to the published value.
set -euo pipefail

EXPECTED="a272bb03051c166b436d1988c3ae606574b43ed9ab5de8f1d418cdcb44efe16f" # pragma: allowlist secret

digest() {
  LC_ALL=C find . -type f \
      ! -path './__MACOSX/*' ! -name '.DS_Store' ! -name 'Thumbs.db' \
      ! -name 'verify.sh' -print \
    | sed 's|^\./||' \
    | LC_ALL=C sort \
    | while IFS= read -r f; do
        printf '%s\0%s\n' "$f" "$(sha256sum "$f" | cut -d' ' -f1)"
      done \
    | sha256sum | cut -d' ' -f1
}

GOT=$(digest)
echo "expected: $EXPECTED"
echo "got:      $GOT"
[ "$GOT" = "$EXPECTED" ] && echo "OK — kit is unmodified" \
                         || { echo "MODIFIED — re-download the kit"; exit 1; }
