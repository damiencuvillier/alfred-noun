#!/bin/bash
# Installation idempotente du backend navigateur : playwright (npm) + Chromium.
# Tout vit dans le dossier data du workflow, jamais dans le workflow lui-même
# (qui est remplacé à chaque mise à jour).
set -euo pipefail

DATA_DIR="${NP_DATA_DIR:-$HOME/Library/Application Support/Alfred/Workflow Data/com.damiencuvillier.alfred.nounproject}"
mkdir -p "$DATA_DIR"
LOG="$DATA_DIR/setup.log"
exec >>"$LOG" 2>&1

# Un échec quelconque laisse un marqueur : les clients arrêtent de relancer
# l'installation en boucle et affichent l'erreur (dernière ligne de ce log).
cleanup() {
  status=$?
  rm -f "$DATA_DIR/setup.pid"
  if [ "$status" -ne 0 ]; then
    touch "$DATA_DIR/.setup-failed"
    echo "ÉCHEC de l'installation (code $status) — corrige puis nounctl → Réinstaller"
  fi
}
trap cleanup EXIT
rm -f "$DATA_DIR/.setup-failed"

echo "=== setup $(date '+%Y-%m-%d %H:%M:%S') ==="

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
NODE_BIN="${NP_NODE:-$(command -v node || true)}"
[ -n "$NODE_BIN" ] || { echo "ERREUR : node introuvable — installe-le (brew install node)"; exit 2; }
NODE_MAJOR="$("$NODE_BIN" --version | sed -E 's/^v([0-9]+).*/\1/')"
echo "node $("$NODE_BIN" --version) ($NODE_BIN)"
if [ "$NODE_MAJOR" -lt 18 ]; then
  echo "ERREUR : node $NODE_MAJOR détecté, 18 minimum requis — mets Node à jour"
  exit 2
fi
export PATH="$(dirname "$NODE_BIN"):$PATH"
command -v npm >/dev/null || { echo "ERREUR : npm introuvable à côté de node"; exit 2; }
echo "registre npm : $(npm config get registry)"

cd "$DATA_DIR"
if [ ! -f package.json ]; then
  cat >package.json <<'EOF'
{
  "name": "alfred-noun-daemon",
  "private": true,
  "dependencies": {
    "playwright": "^1.49.0"
  }
}
EOF
fi

echo "-- npm install…"
npm install --no-audit --no-fund
echo "-- téléchargement de Chromium (réutilise le cache ms-playwright si possible)…"
npx playwright install chromium
touch "$DATA_DIR/.setup-done"
echo "OK — installation terminée"
