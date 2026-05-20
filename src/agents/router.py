"""
Agente Roteador
Classifica a intenção do usuário e decide qual agente acionar.
thinking=OFF — prioridade em latência mínima.
"""

from __future__ import annotations

import json
from src.llm.qwen_client import chat, formatar_mensagens

SYSTEM_PROMPT_ROUTER = """Você é o roteador do BluaDiagnostics, assistente cardiovascular da Care Plus.

Sua única função é classificar a intenção do usuário em uma das categorias abaixo e retornar APENAS um JSON válido, sem texto adicional.

CATEGORIAS:
- checkup: usuário quer fazer check-up, informar sinais vitais ou analisar batimentos
- triagem: usuário relata sintoma agudo cardiovascular (dor no peito, palpitação, falta de ar, tontura, desmaio)
- suporte: usuário tem dúvida sobre medicação, interação medicamentosa ou histórico
- fora_de_escopo: assunto não cardiovascular

FORMATO DE RESPOSTA (apenas JSON):
{"intent": "checkup"|"triagem"|"suporte"|"fora_de_escopo", "confianca": 0.0-1.0}

EXEMPLOS:
Usuário: "Quero fazer meu check-up" → {"intent": "checkup", "confianca": 0.98}
Usuário: "Estou com dor no peito" → {"intent": "triagem", "confianca": 0.97}
Usuário: "Posso tomar ibuprofeno com Losartana?" → {"intent": "suporte", "confianca": 0.95}
Usuário: "Como tratar diabetes?" → {"intent": "fora_de_escopo", "confianca": 0.99}"""


def rotear(mensagem: str, historico: list[dict] | None = None) -> dict:
    """
    Classifica a intenção do usuário.

    Args:
        mensagem: Mensagem atual do usuário.
        historico: Turnos anteriores da conversa.

    Returns:
        Dicionário com intent e confianca.
        Em caso de erro, retorna intent checkup como fallback seguro.
    """
    historico = historico or []

    mensagens = formatar_mensagens(
        system_prompt=SYSTEM_PROMPT_ROUTER,
        historico=historico,
        mensagem_usuario=mensagem,
    )

    try:
        resposta = chat(
            messages=mensagens,
            enable_thinking=False,
            temperature=0.1,
        )

        resultado = json.loads(resposta["content"].strip())

        intent = resultado.get("intent", "checkup")
        if intent not in {"checkup", "triagem", "suporte", "fora_de_escopo"}:
            intent = "checkup"

        return {
            "intent": intent,
            "confianca": resultado.get("confianca", 0.8)
        }

    except Exception as exc:
        print(f"[router] Erro na classificação: {exc}. Usando fallback: checkup")
        return {"intent": "checkup", "confianca": 0.5}