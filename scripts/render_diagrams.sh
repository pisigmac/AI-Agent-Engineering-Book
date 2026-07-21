#!/usr/bin/env bash
# Render all Mermaid sources under diagrams/mermaid/ to PNG under diagrams/png/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MMDC="${ROOT}/node_modules/.bin/mmdc"
if [[ ! -x "$MMDC" ]]; then
  echo "Installing @mermaid-js/mermaid-cli and puppeteer..."
  npm install --no-fund --no-audit @mermaid-js/mermaid-cli puppeteer
fi

ok=0
fail=0
while IFS= read -r -d '' mmd; do
  rel="${mmd#${ROOT}/diagrams/mermaid/}"
  chdir="$(dirname "$rel")"
  base="$(basename "$mmd" .mmd)"
  outdir="${ROOT}/diagrams/png/${chdir}"
  mkdir -p "$outdir"
  out="${outdir}/${base}.png"
  if "$MMDC" -i "$mmd" -o "$out" -b white -s 2 >/dev/null; then
    echo "OK  diagrams/png/${chdir}/${base}.png"
    ok=$((ok + 1))
  else
    echo "FAIL diagrams/mermaid/${rel}"
    fail=$((fail + 1))
  fi
done < <(find "${ROOT}/diagrams/mermaid" -name '*.mmd' -print0 | sort -z)

echo "Rendered: ok=${ok} fail=${fail}"
exit "$([[ "$fail" -eq 0 ]] && echo 0 || echo 1)"
