#!/usr/bin/env bash
set -euo pipefail
mkdir -p assets/icons
shopt -s nullglob 2>/dev/null || true
for f in assets/icons/*.png.b64; do
  out="${f%.b64}"
  if base64 --help 2>&1 | grep -q -- "--decode"; then
    base64 --decode "$f" > "$out"
  else
    # macOS/BSD base64 uses -D to decode
    base64 -D -i "$f" -o "$out" 2>/dev/null || base64 -D "$f" > "$out"
  fi
  echo "Wrote $out"
done

# example: run `./scripts/decode-icons.sh` to create icon-*.png files from the .b64 sources
