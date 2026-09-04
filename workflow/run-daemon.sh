#!/bin/bash
# Lance le démon Playwright en avant-plan (le détachement est fait par l'appelant).
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
DIR="$(cd "$(dirname "$0")" && pwd)"
export NP_DATA_DIR="${NP_DATA_DIR:-$HOME/Library/Application Support/Alfred/Workflow Data/com.damiencuvillier.alfred.nounproject}"
mkdir -p "$NP_DATA_DIR"
NODE_BIN="${NP_NODE:-node}"
exec "$NODE_BIN" "$DIR/server.mjs" >>"$NP_DATA_DIR/daemon.log" 2>&1
