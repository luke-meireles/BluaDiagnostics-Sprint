"""
Agente de Prescrição Cardiovascular
Quinto especialista do BluaDiagnostics, exigido pela Sprint 2.

Gera rascunhos de prescrição pós-teleconsulta — sempre com HITL.
thinking=ON — raciocínio clínico cuidadoso.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.llm.qwen_client import chat, formatar_mensagens, TEMPERATURA_PADRAO
from src.prompts import carregar_prompt
from src.tools import (
    consultar_historico_paciente,
    verificar_interacoes_medicamentosas,
    sugerir_rascunho_prescricao,
)
from src.rag import recuperar_contexto

# Tools spec — carrega só as relevantes para este agente
_TOOLS_SPEC_PATH = Path(__file__).resolve().parents[2] / "tools" / "tools_spec.json"
_TOOLS_SPEC = json.loads(_TOOLS_SPEC_PATH.read_text(encoding="utf-8"))

_TOOLS_PRESCRICAO = [
    {"type": "function", "function": t}
    for t in _TOOLS_SPEC
    if t["name"] in {
        "consultar_historico_paciente",
        "verificar_interacoes_medicamentosas",
        "sugerir_rascunho_prescricao",
    }
]

# System prompt carregado do .md — eliminando hard-coding
SYSTEM_PROMPT_PRESCRICAO = carregar_prompt("agente_prescricao")


def _executar_tool(nome: str, argumentos: dict) -> str:
    """Executa a tool solicitada e retorna resultado como string JSON."""
    mapa = {
        "consultar_historico_paciente": consultar_historico_paciente,
        "verificar_interacoes_medicamentosas": verificar_interacoes_medicamentosas,
        "sugerir_rascunho_prescricao": sugerir_rascunho_prescricao,
    }
    func = mapa.get(nome)
    if not func:
        return json.dumps({"erro": f"Tool '{nome}' não encontrada."})
    try:
        resultado = func(**argumentos)
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"erro": str(exc)})


def agente_prescricao(
    mensagem: str,
    historico: list[dict],
    beneficiario_id: str = "BENEF-001",
) -> dict:
    """
    Executa o agente de prescrição cardiovascular.

    Args:
        mensagem: Mensagem atual do usuário.
        historico: Histórico de turnos anteriores.
        beneficiario_id: ID do beneficiário mockado.

    Returns:
        Dicionário com resposta, tools chamadas, metadados e flag
        'requer_aprovacao_humana' para o nó HITL do grafo.
    """
    # Injetar contexto do beneficiário
    system = SYSTEM_PROMPT_PRESCRICAO + f"\n\nBENEFICIÁRIO ATIVO: {beneficiario_id}"

    # RAG com foco em bulas e protocolos — categoria-friendly para o filtro futuro
    contexto_rag = recuperar_contexto(mensagem, n_resultados=3)
    if contexto_rag:
        system += f"\n\n{contexto_rag}"

    mensagens = formatar_mensagens(system, historico, mensagem)

    resposta = chat(
        messages=mensagens,
        tools=_TOOLS_PRESCRICAO,
        enable_thinking=True,
        temperature=TEMPERATURA_PADRAO,  # 0.3 — baixa, prescrição é determinística
    )

    tools_chamadas = []
    rascunho_emitido = False

    while resposta.get("tool_calls"):
        for tc in resposta["tool_calls"]:
            nome = tc["name"]
            argumentos = json.loads(tc["arguments"])

            print(f"[prescricao] Chamando tool: {nome}({argumentos})")
            resultado_str = _executar_tool(nome, argumentos)
            tools_chamadas.append({"tool": nome, "resultado": resultado_str})

            # Detectar emissão de rascunho — ativa flag HITL para o grafo
            if nome == "sugerir_rascunho_prescricao":
                try:
                    resultado_dict = json.loads(resultado_str)
                    if resultado_dict.get("status") == "RASCUNHO_AGUARDANDO_REVISAO_MEDICA":
                        rascunho_emitido = True
                except json.JSONDecodeError:
                    pass

            mensagens.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": nome, "arguments": tc["arguments"]}
                }]
            })
            mensagens.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": resultado_str
            })

        resposta = chat(
            messages=mensagens,
            tools=_TOOLS_PRESCRICAO,
            enable_thinking=True,
            temperature=TEMPERATURA_PADRAO,
        )

    return {
        "resposta": resposta["content"],
        "agente": "prescricao",
        "tools_chamadas": tools_chamadas,
        "thinking": resposta.get("thinking"),
        "usage": resposta["usage"],
        "requer_aprovacao_humana": rascunho_emitido,
    }
