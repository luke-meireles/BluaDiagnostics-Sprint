"""
Safety Layer - Validador
Valida respostas dos agentes antes de entregar ao usuário.
Detecta red flags não tratadas, jailbreak e conteúdo fora de escopo.
"""

from __future__ import annotations

import re

# Termos que indicam red flag cardiovascular não tratada
_RED_FLAGS_KEYWORDS = [
    "dor no peito", "dor torácica", "infarto", "avc", "acidente vascular",
    "parada cardíaca", "desmaiei", "desmaio", "síncope", "falta de ar súbita",
    "pressão 18", "pressão 19", "irradiando para o braço",
]

# Termos que indicam possível diagnóstico definitivo indevido
_DIAGNOSTICO_DEFINITIVO = [
    "você tem ", "o diagnóstico é ", "confirmado que é ",
    "certamente é ", "definitivamente é ",
]

# Disclaimer obrigatório
_DISCLAIMER = "\n\n⚕️ *Este assistente oferece suporte informativo e não substitui avaliação médica. Em emergência, ligue 192 (SAMU).*"


def agente_safety(
    mensagem_usuario: str,
    resposta_agente: str,
    intent: str,
) -> dict:
    """
    Valida a resposta do agente antes de entregar ao usuário.

    Verificações:
    1. Red flag na mensagem do usuário sem escalada na resposta
    2. Diagnóstico definitivo indevido na resposta
    3. Disclaimer obrigatório presente

    Args:
        mensagem_usuario: Mensagem original do usuário.
        resposta_agente: Resposta gerada pelo agente especializado.
        intent: Intent classificada pelo roteador.

    Returns:
        Dicionário com resposta validada e flags de auditoria.
    """
    flags = []
    resposta_final = resposta_agente

    mensagem_lower = mensagem_usuario.lower()
    resposta_lower = resposta_agente.lower()

    # Verificação 1 — Red flag sem escalada
    red_flag_detectada = any(kw in mensagem_lower for kw in _RED_FLAGS_KEYWORDS)
    escalada_presente = any(
        termo in resposta_lower
        for termo in ["192", "samu", "pronto-socorro", "emergência"]
    )

    if red_flag_detectada and not escalada_presente and intent == "triagem":
        flags.append("RED_FLAG_SEM_ESCALADA")
        # Adicionar instrução de segurança no início
        resposta_final = (
            "⚠️ Os sintomas que você descreveu podem indicar uma situação de urgência cardiovascular. "
            "Se a situação piorar, ligue imediatamente para **192 (SAMU)**.\n\n"
            + resposta_final
        )

    # Verificação 2 — Diagnóstico definitivo indevido
    diagnostico_indevido = any(
        termo in resposta_lower for termo in _DIAGNOSTICO_DEFINITIVO
    )
    if diagnostico_indevido:
        flags.append("DIAGNOSTICO_DEFINITIVO_DETECTADO")

    # Verificação 3 — Disclaimer obrigatório
    disclaimer_presente = "não substitui" in resposta_lower or "samu" in resposta_lower
    if not disclaimer_presente:
        resposta_final += _DISCLAIMER
        flags.append("DISCLAIMER_ADICIONADO")

    return {
        "resposta": resposta_final,
        "flags": flags,
        "red_flag_detectada": red_flag_detectada,
        "aprovado": "RED_FLAG_SEM_ESCALADA" not in flags
                    and "DIAGNOSTICO_DEFINITIVO_DETECTADO" not in flags,
    }