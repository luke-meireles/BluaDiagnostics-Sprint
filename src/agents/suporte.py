"""
Agente de Suporte Clínico Cardiovascular
Verifica interações medicamentosas e consulta histórico.
thinking=ON — raciocínio cuidadoso em contexto medicamentoso.

REFATORADO Sprint 2: system prompt agora carregado de prompts/agente_suporte_clinico.md
"""

from __future__ import annotations

import json
from pathlib import Path

from src.llm.qwen_client import chat, formatar_mensagens, TEMPERATURA_RACIOCINIO
from src.prompts import carregar_prompt
from src.tools import (
    consultar_historico_paciente,
    verificar_interacoes_medicamentosas,
    agendar_teleconsulta,
)
from src.rag import recuperar_contexto

_TOOLS_SPEC_PATH = Path(__file__).resolve().parents[2] / "tools" / "tools_spec.json"
_TOOLS_SPEC = json.loads(_TOOLS_SPEC_PATH.read_text(encoding="utf-8"))

_TOOLS_SUPORTE = [
    {"type": "function", "function": t}
    for t in _TOOLS_SPEC
    if t["name"] in {
        "consultar_historico_paciente",
        "verificar_interacoes_medicamentosas",
        "agendar_teleconsulta",
    }
]

# System prompt agora vem do arquivo prompts/agente_suporte_clinico.md
SYSTEM_PROMPT_SUPORTE = carregar_prompt("agente_suporte_clinico")


def _executar_tool(nome: str, argumentos: dict) -> str:
    mapa = {
        "consultar_historico_paciente": consultar_historico_paciente,
        "verificar_interacoes_medicamentosas": verificar_interacoes_medicamentosas,
        "agendar_teleconsulta": agendar_teleconsulta,
    }
    func = mapa.get(nome)
    if not func:
        return json.dumps({"erro": f"Tool '{nome}' não encontrada."})
    try:
        return json.dumps(func(**argumentos), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"erro": str(exc)})


def agente_suporte_clinico(
    mensagem: str,
    historico: list[dict],
    beneficiario_id: str = "BENEF-001",
) -> dict:
    """
    Executa o agente de suporte clínico cardiovascular.
    """
    system = SYSTEM_PROMPT_SUPORTE + f"\n\nBENEFICIÁRIO ATIVO: {beneficiario_id}"

    contexto_rag = recuperar_contexto(mensagem, n_resultados=3)
    if contexto_rag:
        system += f"\n\n{contexto_rag}"

    mensagens = formatar_mensagens(system, historico, mensagem)

    resposta = chat(
        messages=mensagens,
        tools=_TOOLS_SUPORTE,
        enable_thinking=True,
        temperature=TEMPERATURA_RACIOCINIO,
    )

    tools_chamadas = []

    while resposta.get("tool_calls"):
        for tc in resposta["tool_calls"]:
            nome = tc["name"]
            argumentos = json.loads(tc["arguments"])

            print(f"[suporte] Chamando tool: {nome}({argumentos})")
            resultado = _executar_tool(nome, argumentos)
            tools_chamadas.append({"tool": nome, "resultado": resultado})

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
                "content": resultado
            })

        resposta = chat(
            messages=mensagens,
            tools=_TOOLS_SUPORTE,
            enable_thinking=True,
            temperature=TEMPERATURA_RACIOCINIO,
        )

    return {
        "resposta": resposta["content"],
        "agente": "suporte_clinico",
        "tools_chamadas": tools_chamadas,
        "thinking": resposta.get("thinking"),
        "usage": resposta["usage"],
    }
