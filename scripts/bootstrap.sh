#!/usr/bin/env bash
# Idempotent setup. Safe to run every session; skips anything already present.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/nova_root.sh" 2>/dev/null || true
HERE="${NOVA_ROOT:-$(dirname "$HERE")}/scripts"
ok(){ printf '  ok    %s\n' "$1"; }; miss(){ printf '  MISS  %s — %s\n' "$1" "$2"; }

echo "nova bootstrap"
PY=$(command -v python3 || true)
[ -n "$PY" ] && ok "python3" || { miss "python3" "required"; exit 1; }

MISSING=""
for m in pdfplumber rapidfuzz sklearn; do
  $PY -c "import $m" 2>/dev/null && ok "python: $m" || MISSING="$MISSING $m"
done
if [ -n "$MISSING" ]; then
  echo "  installing:$MISSING"
  PKGS=$(echo "$MISSING" | sed 's/sklearn/scikit-learn/')
  $PY -m pip install --quiet $PKGS 2>/dev/null \
    || $PY -m pip install --quiet --break-system-packages $PKGS 2>/dev/null \
    || echo "  (install failed — cv_score degrades gracefully but scores will be coarser)"
fi
$PY -c "import docx" 2>/dev/null && ok "python: python-docx (.docx input)" \
  || echo "  note: python-docx absent — .docx CVs fall back to LibreOffice"

command -v node >/dev/null && ok "node" || miss "node" "needed to render docx output"
if command -v node >/dev/null; then
  node -e "require('docx')" 2>/dev/null && ok "node: docx" || {
    echo "  installing node docx…"; (cd "$HERE/.." && npm install --silent docx 2>/dev/null) \
      && ok "node: docx" || miss "node: docx" "run: npm install docx"; }
fi
command -v soffice >/dev/null && ok "libreoffice (docx to pdf)" \
  || miss "libreoffice" "docx renders but PDF conversion + ATS parse gate unavailable"

echo "  scorer_version: $($PY -c "import sys;sys.path.insert(0,'$HERE');import cv_score;print(cv_score.scorer_version())" 2>/dev/null || echo unavailable)"
echo "done"
