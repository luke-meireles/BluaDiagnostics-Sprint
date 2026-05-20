"""Interface de reranker — desligada por padrão na PoC.

Quando ativada, recebe `(query, chunk)` e devolve um score de relevância
mais preciso que a similaridade vetorial pura, reordenando os top-k antes
de irem para o LLM. Na Sprint 1 fica como no-op para evitar latência
extra; ativação prevista para Sprint 2 após medição.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RerankerConfig:
    """Configuração da camada de reranker."""

    enabled: bool = False
    model: str = "Qwen3-Reranker-0.6B"
    top_n: int = 4


def rerank(
    query: str,
    chunks: list[dict[str, Any]],
    config: RerankerConfig | None = None,
) -> list[dict[str, Any]]:
    """Reordena os chunks segundo relevância com a query.

    No-op enquanto `config.enabled=False`. A integração com o modelo de
    reranking foi adiada para evitar latência adicional na PoC.
    """
    if config is None:
        config = RerankerConfig()

    if not config.enabled:
        return chunks

    # TODO: integrar Qwen3-Reranker via DashScope quando o trade-off
    # latência/qualidade for validado em homologação.
    return chunks[: config.top_n]
