#!/usr/bin/env bash
# Sube el commit actual (HEAD) a un Space de Docker en Hugging Face.
# Uso: bash scripts/deploy_hf_space.sh usuario/nombre-del-space
# Requiere: pip install huggingface_hub  +  hf auth login (token con permiso write)
set -euo pipefail

SPACE="${1:?Uso: $0 usuario/nombre-del-space}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Solo archivos versionados — nada de .env, index/, venv/ ni node_modules/
git archive HEAD | tar -x -C "$TMP"

# El Space lee su config del frontmatter YAML del README
{
  cat <<'YAML'
---
title: Differential
emoji: 🩺
colorFrom: blue
colorTo: yellow
sdk: docker
app_port: 5000
pinned: false
license: mit
short_description: Práctica de diagnóstico diferencial con RAG
---

YAML
  cat "$TMP/README.md"
} > "$TMP/README.space.md"
mv "$TMP/README.space.md" "$TMP/README.md"

hf upload "$SPACE" "$TMP" . --repo-type space --delete "*" \
  --commit-message "deploy: $(git rev-parse --short HEAD)"

echo "Listo: https://huggingface.co/spaces/$SPACE"
