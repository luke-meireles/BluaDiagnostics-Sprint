"""
Responsabilidades:
- Conexão com DashScope International (qwen-plus)
- Suporte a function calling (tools)
- Suporte a hybrid thinking mode (thinking=ON/OFF por agente)
- Tratamento de erros e retries
- Interface única para todos os agentes

Uso:
    from src.llm.qwen_client import chat

    resposta = chat(
        messages=[{"role": "user", "content": "Olá"}],
        tools=None,
        enable_thinking=False,
        temperature=0.3
    )
"""

from __future__ import annotations

import os
import time
from typing import Any, Literal
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# CONSTANTES

# Modelo fixo — alterado apenas via variável de ambiente
def _modelo_padrao(backend: str) -> str:
    """Lê o modelo no momento da chamada (não no import).

    Necessário porque `colab_setup.preparar_ambiente()` pode rodar
    depois do primeiro `import` deste módulo — se lêssemos no import,
    a variável atualizada seria ignorada.
    """
    if backend == "dashscope":
        return os.getenv("QWEN_DASHSCOPE_MODEL", "qwen-plus")
    return os.getenv("QWEN_OLLAMA_MODEL", "qwen:9b")

# Base URL do DashScope International
_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# Temperatura padrão por tipo de agente
# Roteador e checkup: baixa — respostas determinísticas
# Triagem e suporte: média — raciocínio mais elaborado
TEMPERATURA_PADRAO = 0.3
TEMPERATURA_RACIOCINIO = 0.5

# Máximo de tokens por resposta
MAX_TOKENS_PADRAO = 1024
MAX_TOKENS_RACIOCINIO = 2048 # thinking = ON gasta mais tokens

# Cliente OpenAI-compatible (DashScope)
def _obter_cliente() -> OpenAI:
    """
    Instancia o cliente OpenAI apontando para DashScope.
    Lança RuntimeError se a chave não estiver configurada.
    """
    chave = os.getenv("DASHSCOPE_API_KEY")
    if not chave:
        raise RuntimeError(
            "DASHSCOPE_API_KEY não encontrada."
            "No Colab, configure em Secrets (ícone 🔑) com Notebook access habilitado."
        )
    return OpenAI(api_key= chave, base_url= _BASE_URL)

# Função principal de chat
@retry(
    retry = retry_if_exception_type(Exception),
    stop = stop_after_attempt(3),
    wait = wait_exponential(multiplier = 1, min = 2, max = 10),
    reraise = True,
)

def chat(
    messages: list[dict[str, Any]],
    tools: list[dict] | None = None,
    enable_thinking: bool = False,
    temperature: float = TEMPERATURA_PADRAO,
    max_tokens: int | None = None,
    modelo: str | None = None,
    backend: Literal["dashscope", "ollama"] = "dashscope",
) -> dict[str, Any]:
    """
    Envia mensagens ao Qwen via DashScope e retorna a resposta

    Args:
        messages: Histórico de mensagens no formato OpenAI
                  [{"role": "system"|"user"|"assistant", "content": "..."}]
        tools: Lista de tools no formato JSON Schema OpenAI/Anthropic.
               None desativa function calling.
        enable_thinking: Liga o hybrid thinking mode do Qwen.
                         Use True em agentes de triagem e suporte clínico.
                         Use False no roteador para latência mínima.
        temperature: Temperatura de geração. 0.0 a 1.0.
        max_tokens: Limite de tokens na resposta.
                    Se None, usa MAX_TOKENS_THINKING se thinking=True,
                    senão MAX_TOKENS_PADRAO.
        modelo: Sobrescreve o modelo padrão. Usar com cautela.

    Returns:
        Dicionário com:
        - content (str): texto da resposta
        - tool_calls (list | None): chamadas de tools se houver
        - thinking (str | None): conteúdo do bloco de raciocínio
        - usage (dict): tokens consumidos
        - finish_reason (str): motivo de parada

    Raises:
        RuntimeError: chave não configurada
        Exception: erro de API após 3 tentativas
    """

    cliente = _obter_cliente()

    # Ajustar o max_tokens de acordo com o thinking mode
    if max_tokens is None:
        max_tokens = MAX_TOKENS_RACIOCINIO if enable_thinking else MAX_TOKENS_PADRAO

    # Parâmetros da chamada
    params: dict[str, Any] = {
        "model": modelo or _modelo_padrao(backend),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Adiciona tools se forem fornecidas
    if tools:
        params["tools"] = tools
        params["tool_choice"] = "auto"

    # Hybrid thinking mode - parâmetro do Qwen
    # Quando True, o modelo raciocina antes de responder.
    # Gerando um bloco <think>...<think> interno
    if enable_thinking:
        params["extra_body"] = {"enable_thinking": True}

    # Chamada à API
    resposta = cliente.chat.completions.create(**params)
    mensagem = resposta.choices[0].message

    # Extrair o conteúdo de thinking, se houver
    # O Qwen retorna o bloco de raciocínio em reasoning_content

    thinking = None
    if hasattr(mensagem, "reasoning_content"):
        thinking = mensagem.reasoning_content

    # Extrair tool calls, se houver
    tool_calls = None
    if hasattr(mensagem, "tool_calls") and mensagem.tool_calls:
        tool_calls = [
            {
                "id": tc.id,
                "name": tc.function.name,
                "arguments": tc.function.arguments
            }
            for tc in mensagem.tool_calls
        ]
    return {
        "content": mensagem.content or "",
        "tool_calls": tool_calls,
        "thinking": thinking,
        "usage":{
            "prompt_tokens": resposta.usage.prompt_tokens,
            "completion_tokens": resposta.usage.completion_tokens,
            "total_tokens": resposta.usage.total_tokens

        },
        "finish_reason": resposta.choices[0].finish_reason
    }

# Utilitários

def smoke_test() -> bool:
    """
    Ping ao modelo para validar credenciais e conectividade.
    Retorna True se bem-sucedido, False no contrário
    """

    try:
        resposta = chat(
            messages=[
                {
                    "role": "system",
                    "content": "Responda em ma frase curta, em português brasileiro."
                },
                {
                    "role": "user",
                    "content": "Você está funcionando?"
                }
            ],
            enable_thinking= False,
            temperature= 0.1
        )
        print(f"[smoke_test] OK -> resposta: {resposta['content']!r}")
        print(f"[smoke_test] Tokens: {resposta['usage']}")
        return True

    except Exception as e:
        print(f"[smoke_test] FALHOU: {type(e).__name__}: {e}")
        return False

def formatar_mensagens(
        system_prompt: str,
        historico: list[dict],
        mensagem_usuario: str
) -> list[dict]:
    """
    Monta a lista de mensagens no formato esperado pela API.

    Args:
        system_prompt: Conteúdo do system prompt do agente.
        historico: Lista de turnos anteriores
                   [{"role": "user"|"assistant", "content": "..."}]
        mensagem_usuario: Mensagem atual do usuário.

    Returns:
        Lista formatada pronta para passar ao chat().
    """
    mensagens = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    mensagens.extend(historico)
    mensagens.append({
        "role": "user",
        "content": mensagem_usuario
    })
    return mensagens


class QwenClient:
    """Versão OO da função `chat`, útil para fixar o backend uma vez.

    Equivalente funcional a chamar `chat(..., backend=self.backend)` em
    todo lugar — existe só para deixar explícito (e auditável via grep)
    qual backend cada consumidor usa.
    """

    def __init__(self, backend: Literal["dashscope", "ollama"] = "dashscope") -> None:
        self.backend = backend

    def chat(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("backend", self.backend)
        return chat(**kwargs)