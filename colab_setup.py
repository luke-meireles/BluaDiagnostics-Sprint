"""
Bootstrap de ambiente — Sprint 2.

Configura:
- Chaves de API (DashScope, opcionalmente Ollama, LangSmith)
- Path do projeto
- Variáveis para hybrid thinking
- LangSmith para observabilidade (se LANGSMITH_API_KEY estiver setada)

Uso:
    from colab_setup import preparar_ambiente
    preparar_ambiente(exigir_chave=True)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    _DOTENV_AVAILABLE = True
except ImportError:
    _DOTENV_AVAILABLE = False


def _carregar_dotenv():
    """Carrega .env se existir e python-dotenv estiver disponível."""
    if not _DOTENV_AVAILABLE:
        return
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def _setup_langsmith() -> bool:
    """
    Ativa observabilidade LangSmith se LANGSMITH_API_KEY estiver configurada.

    LangSmith instrumenta LangGraph automaticamente — sem código novo.
    Free tier: 5000 traces/mês.
    """
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv(
        "LANGSMITH_PROJECT", "BluaDiagnostics-Sprint2"
    )
    return True


def _try_colab_secrets():
    """Tenta carregar chaves do Colab Secrets se rodando no Colab."""
    try:
        from google.colab import userdata  # type: ignore
        for key in ["DASHSCOPE_API_KEY", "LANGSMITH_API_KEY"]:
            if not os.getenv(key):
                try:
                    val = userdata.get(key)
                    if val:
                        os.environ[key] = val
                        print(f"[colab_setup] {key} carregada de Colab Secrets")
                except Exception:
                    pass
    except ImportError:
        pass  # Não estamos no Colab


def preparar_ambiente(exigir_chave: bool = True) -> dict:
    """
    Prepara o ambiente para execução do BluaDiagnostics.

    Args:
        exigir_chave: Se True, levanta RuntimeError quando DASHSCOPE_API_KEY
                      não está configurada E backend é dashscope.

    Returns:
        Dicionário com status do bootstrap.
    """
    raiz = Path(__file__).resolve().parent
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))

    _carregar_dotenv()
    _try_colab_secrets()

    backend = os.getenv("LLM_BACKEND", "dashscope")

    if backend == "dashscope":
        chave = os.getenv("DASHSCOPE_API_KEY")
        if not chave and exigir_chave:
            raise RuntimeError(
                "DASHSCOPE_API_KEY não configurada. "
                "Defina via .env, Colab Secrets ou variável de ambiente. "
                "Alternativa: defina LLM_BACKEND=ollama para uso local."
            )

    langsmith_ativo = _setup_langsmith()

    print(f"[colab_setup] Ambiente preparado")
    print(f"  Backend LLM: {backend}")
    if langsmith_ativo:
        print(f"  LangSmith: ATIVO (projeto: {os.getenv('LANGCHAIN_PROJECT')})")
    else:
        print(f"  LangSmith: desativado (sem LANGSMITH_API_KEY)")

    return {
        "backend": backend,
        "langsmith_ativo": langsmith_ativo,
        "raiz": str(raiz),
    }
