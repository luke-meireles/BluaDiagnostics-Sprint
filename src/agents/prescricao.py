"""
Agente de Prescrição Cardiovascular — Sprint 2.

Mudanças vs Lote 1:
- Usa recuperar_contexto_detalhado.
- Filtro: bula + protocolo + politica_care_plus (foco em info farmacológica).
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
from src.rag import recuperar_contexto_detalhado

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

SYSTEM_PROMPT_PRESCRICAO = carregar_prompt("agente_prescricao")


def _executar_tool(nome: str, argumentos: dict) -> str:
    mapa = {
        "consultar_historico_paciente": consultar_historico_paciente,
        "verificar_interacoes_medicamentosas": verificar_interacoes_medicamentosas,
        "sugerir_rascunho_prescricao": sugerir_rascunho_prescricao,
    }
    func = mapa.get(nome)
    if not func:
        return json.dumps({"erro": f"Tool '{nome}' não encontrada."})
    try:
        return json.dumps(func(**argumentos), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"erro": str(exc)})


def agente_prescricao(
    mensagem: str,
    historico: list[dict],
    beneficiario_id: str = "BENEF-MARIA",
) -> dict:
    system = SYSTEM_PROMPT_PRESCRICAO + f"\n\nBENEFICIÁRIO ATIVO: {beneficiario_id}"

    contexto_rag, documentos_rag = recuperar_contexto_detalhado(
        query=mensagem,
        n_resultados=3,
        filtro_categoria=["bula", "protocolo", "politica_care_plus"],
        usar_mmr=True,
        usar_auto_rag=True,
        usar_reranker=False,
    )
    if contexto_rag:
        system += f"\n\n{contexto_rag}"

    mensagens = formatar_mensagens(system, historico, mensagem)

    resposta = chat(
        messages=mensagens,
        tools=_TOOLS_PRESCRICAO,
        enable_thinking=True,
        temperature=TEMPERATURA_PADRAO,
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

            if nome == "sugerir_rascunho_prescricao":
                try:
                    if "RASCUNHO_AGUARDANDO_REVISAO_MEDICA" in resultado_str:
                        rascunho_emitido = True
                except Exception:
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
        "documentos_rag": documentos_rag,
        "thinking": resposta.get("thinking"),
        "usage": resposta["usage"],
        "requer_aprovacao_humana": rascunho_emitido,
    }
