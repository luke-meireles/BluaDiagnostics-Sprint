"""
Bootstrap do ambiente para Google Colab e execução local.


Responsabilidades:
- Localizar a raiz do projeto
- Configurar sys.path para imports de src/
- Carregar DASHSCOPE_API_KEY (Colab Secrets → .env)
- Criar diretórios necessários (logs/, chroma_db/)
- Validar dependências críticas

Uso no notebook (primeira célula):
    from colab_setup import preparar_ambiente
    preparar_ambiente()
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


# ----------------------------------------------------------------
# Detecção de ambiente
# ----------------------------------------------------------------

def em_colab() -> bool:
    """Retorna True se executando no Google Colab."""
    try:
        import google.colab # type: ignore (type:ignore suprime o aviso de type checker no vscode) # noqa: F401 (suprime o aviso de import não utilizado)
        return True
    except ImportError:
        return False


# ----------------------------------------------------------------
# Localização da raiz do projeto
# ----------------------------------------------------------------

def _localizar_raiz() -> Path:
    """
    Localiza a raiz do projeto BluaDiagnostics.
    Tenta em ordem: arquivo atual → CWD → /content/bluadiagnostics.
    """
    # Diretório do próprio colab_setup.py
    aqui = Path(__file__).resolve().parent
    if (aqui / "src" / "graph.py").exists():
        return aqui

    # CWD e ancestrais
    for candidato in [Path.cwd(), *Path.cwd().parents]:
        if (candidato / "src" / "graph.py").exists():
            return candidato

    # Fallback para Colab
    if em_colab():
        destino = Path("/content/bluadiagnostics")
        if (destino / "src" / "graph.py").exists():
            return destino

    raise FileNotFoundError(
        "Raiz do projeto não encontrada. "
        "Certifique-se de que o projeto está em /content/bluadiagnostics "
        "ou execute colab_setup.py a partir da raiz do projeto."
    )


# ----------------------------------------------------------------
# Carregamento da chave DashScope
# ----------------------------------------------------------------

def _carregar_chave() -> str | None:
    """
    Resolve DASHSCOPE_API_KEY em ordem de prioridade:
    1. Variável de ambiente já definida
    2. Colab Secrets (ambiente Colab)
    3. Arquivo .env (ambiente local)
    """
    # 1. Variável de ambiente
    chave = os.getenv("DASHSCOPE_API_KEY")
    if chave:
        return chave

    # 2. Colab Secrets
    if em_colab():
        try:
            from google.colab import userdata  # type: ignore
            chave = userdata.get("DASHSCOPE_API_KEY")
            if chave:
                os.environ["DASHSCOPE_API_KEY"] = chave
                return chave
        except Exception:
            pass

    # 3. Arquivo .env local
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(override=False)
        return os.getenv("DASHSCOPE_API_KEY")
    except ImportError:
        return None


# ----------------------------------------------------------------
# Função principal
# ----------------------------------------------------------------

def preparar_ambiente(exigir_chave: bool = True) -> dict[str, Any]:
    """
    Prepara o ambiente BluaDiagnostics de forma idempotente.

    Args:
        exigir_chave: Se True, lança RuntimeError quando
                      DASHSCOPE_API_KEY não for encontrada.
                      Use False apenas para --help ou testes secos.

    Returns:
        Diagnóstico do ambiente configurado.
    """
    # Localizar raiz e configurar sys.path
    raiz = _localizar_raiz()

    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))

    os.chdir(raiz)

    # Definir modelo padrão
    os.environ.setdefault("QWEN_DASHSCOPE_MODEL", "qwen-plus")

    # Criar diretórios necessários
    (raiz / "logs").mkdir(parents=True, exist_ok=True)

    chroma_dir = Path(
        os.getenv("CHROMA_PERSIST_DIR", str(raiz / "chroma_db"))
    )
    chroma_dir.mkdir(parents=True, exist_ok=True)

    # Carregar chave
    chave = _carregar_chave()

    if exigir_chave and not chave:
        raise RuntimeError(
            "DASHSCOPE_API_KEY não encontrada.\n"
            "No Colab: adicione em Secrets (ícone 🔑) com "
            "Notebook access habilitado.\n"
            "Local: crie um arquivo .env com DASHSCOPE_API_KEY=sua_chave."
        )

    diagnostico = {
        "ambiente": "colab" if em_colab() else "local",
        "raiz_projeto": str(raiz),
        "chave_carregada": bool(chave),
        "modelo": os.environ.get("QWEN_DASHSCOPE_MODEL"),
        "python": sys.version.split()[0],
        "chroma_dir": str(chroma_dir),
        "logs_dir": str(raiz / "logs"),
    }

    print("[colab_setup] Ambiente preparado:")
    for k, v in diagnostico.items():
        print(f"  {k}: {v}")

    return diagnostico


__all__ = ["preparar_ambiente", "em_colab"]