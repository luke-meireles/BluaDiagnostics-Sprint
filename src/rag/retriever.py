"""
Responsabilidades:
- Receber query do agente
- Buscar chunks relevantes na coleção ChromaDB
- Retornar contexto formatado para injeção no prompt

Uso:
    from src.rag import recuperar_contexto
    contexto = recuperar_contexto("sintomas de infarto", n_resultados=3)
"""

from __future__ import annotations

import os
from pathlib import Path

from chromadb import PersistentClient
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from .indexer import CHROMA_DIR, COLECAO_NOME, MODELO_EMBEDDINGS

# Número padrão de chunks a recuperar por query
N_RESULTADOS_PADRAO = 3

# Distância máxima aceitável — chunks muito distantes são descartados
# ChromaDB usa distância coseno: 0 = idêntico, 2 = oposto
DISTANCIA_MAXIMA = 1.2


def recuperar_contexto(
    query: str,
    n_resultados: int = N_RESULTADOS_PADRAO,
    filtro_fonte: str | None = None,
) -> str:
    """
    Recupera contexto clínico cardiovascular relevante para a query.

    Args:
        query: Pergunta ou contexto do agente para busca semântica.
        n_resultados: Número de chunks a recuperar.
        filtro_fonte: Filtrar por documento específico. Ex: 'red_flags_cardiovasculares.md'

    Returns:
        String formatada com os chunks relevantes para injeção no prompt.
        Retorna string vazia se nenhum resultado relevante for encontrado.
    """
    try:
        cliente = PersistentClient(path=str(CHROMA_DIR))

        # Verificar se coleção existe
        colecoes = [c.name for c in cliente.list_collections()]
        if COLECAO_NOME not in colecoes:
            print("[retriever] Aviso: knowledge base não indexada. "
                  "Execute indexar_knowledge_base() primeiro.")
            return ""

        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=MODELO_EMBEDDINGS
        )
        colecao = cliente.get_collection(
            name=COLECAO_NOME,
            embedding_function=embedding_fn
        )

        # Montar filtro por fonte se solicitado
        where = {"fonte": filtro_fonte} if filtro_fonte else None

        # Busca semântica
        resultados = colecao.query(
            query_texts=[query],
            n_results=n_resultados,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        # Filtrar por distância máxima e formatar
        chunks_relevantes = []

        for doc, meta, dist in zip(
            resultados["documents"][0],
            resultados["metadatas"][0],
            resultados["distances"][0]
        ):
            if dist <= DISTANCIA_MAXIMA:
                chunks_relevantes.append(
                    f"[Fonte: {meta['titulo']}]\n{doc}"
                )

        if not chunks_relevantes:
            return ""

        # Formatar contexto para injeção no prompt
        contexto = "\n\n---\n\n".join(chunks_relevantes)
        return f"CONTEXTO CLÍNICO RELEVANTE:\n\n{contexto}"

    except Exception as exc:
        print(f"[retriever] Erro na busca: {type(exc).__name__}: {exc}")
        return ""