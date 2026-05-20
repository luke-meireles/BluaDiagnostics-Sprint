"""
Exporta indexer e retriever para uso dos agentes
"""

from .indexer import indexar_knowledge_base
from .retriever import recuperar_contexto

__all__ = ["indexar_knowledge_base", "recuperar_contexto"]