"""
Indexação da knowledge base cardiovascular no ChromaDB.

Responsabilidades:
- Carregar os 7 documentos da knowledge_base/
- Dividir em chunks via RecursiveCharacterTextSplitter
- Gerar embeddings com multilingual-e5-large
- Persistir no ChromaDB local

Uso:
    from src.rag import indexar_knowledge_base
    indexar_knowledge_base()  # executar uma vez por sessão do Colab
"""

from __future__ import annotations
import os
from pathlib import Path
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configurações

# Diretório da knowledge base
KB_DIR = Path(__file__).resolve().parents[2] / "knowledge_base"

# Diretório de persistência do ChromaDB
CHROMA_DIR = Path(
    os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parents[2] / "chroma_db"))
)

# Nome da coleção ChromaDB
COLECAO_NOME = "bluadiagnostics_cardiovascular"

# Modelo de embeddings - multilingual, suporta PT-BR nativamente
MODELO_EMBEDDINGS = "intfloat/multilingual-e5-large"

# Configuração do splitter (divisor)
CHUNK_SIZE = 800     # caracteres por chunk (bloco: divisão de um grande volume de dados em partes menores e mais gerenciáveis)
CHUNK_OVERLAP = 100  # sobreposição entre chunks para manter contexto

# Funções

def _carregar_documentos () -> list[dict]:
    """
    Carrega todos os arquivos .md da knowledge_base/.
    Retorna lista de dicionários com conteúdo e metadados.
    """
    documentos = []
    for arquivo in sorted(KB_DIR.glob("*.md")):
        conteudo = arquivo.read_text(encoding= "utf-8")
        documentos.append({
            "conteudo": conteudo,
            "fonte": arquivo.name,
            "titulo": arquivo.stem.replace("_", " ").title()
        })
        print(f" [indexer] Carregado: {arquivo.name} ({len(conteudo)} chars)")
    return documentos

def _dividir_chunks(documentos: list[dict]) -> tuple[list[str], list[dict]]:
    """
    Divide documentos em chunks menores para indexação.
    Retorna textos e metadados correspondentes.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP,
        separators= ["\n## ", "\n### ", "\n\n", "\n", " "]
    )

    textos = []
    metadados = []

    for doc in documentos:
        chunks = splitter.split_text(doc["conteudo"])

        for i, chunk in enumerate(chunks):
            # Texto do chunk
            textos.append(chunk)

            # Metadados do chunk
            metadados.append({
                "fonte": doc["fonte"],
                "titulo": doc["titulo"],
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
    return textos, metadados

def indexar_knowledge_base(forcar_reindexacao: bool = False) -> int:
    """
    Indexa a knowledge base cardiovascular no ChromaDB.
    Idempotente — verifica se já foi indexado antes de reprocessar.

    Args:
        forcar_reindexacao: Se True, recria a coleção do zero.

    Returns:
        Número total de chunks indexados.
    """
    print("[indexer] Iniciando a indexação da knowledge_base cardiovascular...")

    # Criar diretório do ChromaDB se não existir
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # Instanciar cliente ChromaDB persistente
    cliente = PersistentClient(path=str(CHROMA_DIR))

    # Verificar se coleção já existe e tem dados
    colecoes_existentes = [c.name for c in cliente.list_collections()]

    if COLECAO_NOME in colecoes_existentes and not forcar_reindexacao:
        colecao = cliente.get_collection(COLECAO_NOME)
        total = colecao.count()
        if total > 0:
            print(f"[indexer] Coleção já indexada com {total} chunks." f"\nUse forcar_indexacao = True para reindexar.")
            return total
        
    # Recriar coleção se forçado
    if COLECAO_NOME in colecoes_existentes and forcar_reindexacao:
        cliente.delete_collection(COLECAO_NOME)
        print("[indexer] Coleção anterior removida.")

    # Criar coleção com função de embeddings
    print(f"[indexer] Carregando modelo de embeddings: {MODELO_EMBEDDINGS}")
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name=MODELO_EMBEDDINGS
    )

    colecao = cliente.create_collection(
        name=COLECAO_NOME,
        embedding_function=embedding_fn,
        metadata={"descricao": "Knowledge base cardiovascular BluaDiagnostics"}
    )

    # Carregar e dividir documentos
    print("[indexer] Carregando documentos...")
    documentos = _carregar_documentos()

    print("[indexer] Dividindo em chunks...")
    textos, metadados = _dividir_chunks(documentos)

    # Gerar IDs únicos para cada chunk
    ids = [f"chunk_{i:04d}" for i in range(len(textos))]

    # Indexar no ChromaDB em lotes de 100
    LOTE = 100
    for inicio in range(0, len(textos), LOTE):
        fim = min(inicio + LOTE, len(textos))
        colecao.add(
            documents=textos[inicio:fim],
            metadatas=metadados[inicio:fim],
            ids=ids[inicio:fim]
        )
        print(f"[indexer] Indexado lote {inicio}–{fim} de {len(textos)}")

    print(f"[indexer] Concluído — {len(textos)} chunks indexados em {CHROMA_DIR}")
    return len(textos)