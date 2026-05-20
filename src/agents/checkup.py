"""
Agente de Check-up
Conduz check-up cardiovascular conversacional.
Chama tools: consultar_historico_paciente, analisar_ritmo_cardiaco,
             consultar_sinais_vitais_wearable, agendar_teleconsulta.
thinking=OFF — fluxo guiado e determinístico.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.llm.qwen_client import chat, formatar_mensagens
from src.tools import (
    consultar_historico_paciente,
    analisar_ritmo_cardiaco,
    consultar_sinais_vitais_wearable,
    agendar_teleconsulta,
)
from src.rag import recuperar_contexto

# Carregar tools_spec para enviar ao modelo
_TOOLS_SPEC_PATH = Path(__file__).resolve().parents[2] / "tools" / "tools_spec.json"
_TOOLS_SPEC = json.loads(_TOOLS_SPEC_PATH.read_text(encoding="utf-8"))

# Filtrar apenas as tools relevantes para este agente
_TOOLS_CHECKUP = [
    {
        "type": "function",
        "function": t
    }
    for t in _TOOLS_SPEC
    if t["name"] in {
        "consultar_historico_paciente",
        "analisar_ritmo_cardiaco",
        "consultar_sinais_vitais_wearable",
        "agendar_teleconsulta",
    }
]

SYSTEM_PROMPT_CHECKUP = """Você é o Agente de Check-up do BluaDiagnostics, assistente cardiovascular digital da Care Plus.

PAPEL: Conduzir check-up cardiovascular conversacional guiado para o beneficiário.

ESCOPO:
- Coletar sintomas cardiovasculares e sinais vitais relatados
- Consultar histórico cardiovascular do beneficiário
- Analisar ritmo cardíaco quando dados de batimentos forem informados
- Consultar leituras de wearable quando disponíveis
- Agendar teleconsulta se necessário

RESTRIÇÕES:
- NUNCA emita diagnóstico definitivo — use "pode indicar", "sugere avaliação"
- NUNCA prescreva ou sugira alteração de medicamento
- Uma pergunta por vez — não sobrecarregue o beneficiário
- Máximo 150 palavras por resposta

FORMATO:
- Tom acolhedor e linguagem acessível
- Red flags sempre no início da resposta com linguagem urgente
- Disclaimer obrigatório ao final: ⚕️ Este assistente não substitui avaliação médica.

ESCALADA:
- Red flag detectada → instrua SAMU 192 imediatamente
- Ritmo irregular → agende teleconsulta urgente ou prioritária"""


def _executar_tool(nome: str, argumentos: dict) -> str:
    """Executa a tool solicitada e retorna resultado como string JSON."""
    mapa = {
        "consultar_historico_paciente": consultar_historico_paciente,
        "analisar_ritmo_cardiaco": analisar_ritmo_cardiaco,
        "consultar_sinais_vitais_wearable": consultar_sinais_vitais_wearable,
        "agendar_teleconsulta": agendar_teleconsulta,
    }

    func = mapa.get(nome)
    if not func:
        return json.dumps({"erro": f"Tool '{nome}' não encontrada."})

    try:
        resultado = func(**argumentos)
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"erro": str(exc)})


def agente_checkup(
    mensagem: str,
    historico: list[dict],
    beneficiario_id: str = "BENEF-001",
) -> dict:
    """
    Executa o agente de check-up cardiovascular.

    Args:
        mensagem: Mensagem atual do usuário.
        historico: Histórico de turnos anteriores.
        beneficiario_id: ID do beneficiário mockado.

    Returns:
        Dicionário com resposta final e metadados.
    """
    # Injetar contexto do beneficiário na mensagem do sistema
    system = SYSTEM_PROMPT_CHECKUP + f"\n\nBENEFICIÁRIO ATIVO: {beneficiario_id}"

    # Recuperar contexto RAG relevante
    contexto_rag = recuperar_contexto(mensagem, n_resultados=2)
    if contexto_rag:
        system += f"\n\n{contexto_rag}"

    mensagens = formatar_mensagens(system, historico, mensagem)

    # Primeira chamada ao modelo
    resposta = chat(
        messages=mensagens,
        tools=_TOOLS_CHECKUP,
        enable_thinking=False,
        temperature=0.3,
    )

    tools_chamadas = []

    # Loop de tool calling
    while resposta.get("tool_calls"):
        for tc in resposta["tool_calls"]:
            nome = tc["name"]
            argumentos = json.loads(tc["arguments"])

            print(f"[checkup] Chamando tool: {nome}({argumentos})")
            resultado = _executar_tool(nome, argumentos)
            tools_chamadas.append({"tool": nome, "resultado": resultado})

            # Adicionar resultado da tool ao histórico da chamada
            mensagens.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": nome,
                        "arguments": tc["arguments"]
                    }
                }]
            })
            mensagens.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": resultado
            })

        # Nova chamada com resultados das tools
        resposta = chat(
            messages=mensagens,
            tools=_TOOLS_CHECKUP,
            enable_thinking=False,
            temperature=0.3,
        )

    return {
        "resposta": resposta["content"],
        "agente": "checkup",
        "tools_chamadas": tools_chamadas,
        "usage": resposta["usage"],
    }