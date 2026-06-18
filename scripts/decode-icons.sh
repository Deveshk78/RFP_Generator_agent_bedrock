#!/usr/bin/env bash
set -euo pipefail
mkdir -p assets/icons
for f in assets/icons/*.png.b64; do
  out="${f%.b64}"
  base64 --decode "$f" > "$out"
  echo "Wrote $out"
done

# example: run `./scripts/decode-icons.sh` to create icon-*.png files from the .b64 sources
