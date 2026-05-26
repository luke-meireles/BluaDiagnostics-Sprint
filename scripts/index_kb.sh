#!/bin/bash
# Script para popular o ChromaDB com a knowledge base cardiovascular
# Uso:
#     bash scripts/index_kb.sh
#     bash scripts/index_kb.sh --force   # força reindexação

set -e

cd "$(dirname "$0")/.."

if [ "$1" == "--force" ]; then
    echo "[index_kb] Forçando reindexação..."
    python -c "from src.rag import indexar_knowledge_base; n = indexar_knowledge_base(forcar_reindexacao=True); print(f'\\n{n} chunks indexados.')"
else
    echo "[index_kb] Indexando knowledge base..."
    python -c "from src.rag import indexar_knowledge_base; n = indexar_knowledge_base(); print(f'\\n{n} chunks indexados.')"
fi
