"""
Grafo LangGraph orquestrando os agentes especializados.
Versão: 1.0.0 | 2026-05-15

Fluxo:
    Usuario → Roteador → (Checkup | Triagem | Suporte | ForaEscopo)
           → Safety Layer → Audit Log → Resposta

Uso:
    from src.graph import construir_grafo, executar_turno

    grafo = construir_grafo()
    estado = executar_turno(grafo, "Quero fazer meu check-up", "thread-001")
    print(estado["resposta_final"])
"""

from __future__ import annotations

from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents import (
    rotear,
    agente_checkup,
    agente_triagem,
    agente_suporte_clinico,
    agente_safety,
)
from src.audit_log import registrar_turno


# Estado do grafo

class EstadoBlua(TypedDict):
    """
    Estado compartilhado entre todos os nós do grafo.
    Cada campo é atualizado pelos nós conforme o fluxo avança.
    """
    # Entrada
    mensagem_usuario: str
    beneficiario_id: str

    # Roteamento
    intent_classificada: str
    confianca_intent: float

    # Histórico de conversa — acumulado via operador de adição
    historico: Annotated[list[dict], operator.add]

    # Resposta do agente especializado
    resposta_agente: str
    agente_ativo: str
    tools_chamadas: list[dict]

    # Safety
    resposta_validada: str
    flags_safety: list[str]
    aprovado: bool

    # Saída final
    resposta_final: str


# Nós do grafo

def no_roteador(estado: EstadoBlua) -> dict:
    """
    Classifica a intenção do usuário e determina qual agente acionar.
    """
    resultado = rotear(
        mensagem=estado["mensagem_usuario"],
        historico=estado.get("historico", []),
    )

    print(f"[graph] Intent: {resultado['intent']} "
          f"(confiança: {resultado['confianca']:.2f})")

    return {
        "intent_classificada": resultado["intent"],
        "confianca_intent": resultado["confianca"],
    }


def no_checkup(estado: EstadoBlua) -> dict:
    """Executa o agente de check-up cardiovascular."""
    resultado = agente_checkup(
        mensagem=estado["mensagem_usuario"],
        historico=estado.get("historico", []),
        beneficiario_id=estado.get("beneficiario_id", "BENEF-001"),
    )
    return {
        "resposta_agente": resultado["resposta"],
        "agente_ativo": "checkup",
        "tools_chamadas": resultado.get("tools_chamadas", []),
    }


def no_triagem(estado: EstadoBlua) -> dict:
    """Executa o agente de triagem cardiovascular."""
    resultado = agente_triagem(
        mensagem=estado["mensagem_usuario"],
        historico=estado.get("historico", []),
        beneficiario_id=estado.get("beneficiario_id", "BENEF-001"),
    )
    return {
        "resposta_agente": resultado["resposta"],
        "agente_ativo": "triagem",
        "tools_chamadas": resultado.get("tools_chamadas", []),
    }


def no_suporte(estado: EstadoBlua) -> dict:
    """Executa o agente de suporte clínico cardiovascular."""
    resultado = agente_suporte_clinico(
        mensagem=estado["mensagem_usuario"],
        historico=estado.get("historico", []),
        beneficiario_id=estado.get("beneficiario_id", "BENEF-001"),
    )
    return {
        "resposta_agente": resultado["resposta"],
        "agente_ativo": "suporte_clinico",
        "tools_chamadas": resultado.get("tools_chamadas", []),
    }


def no_fora_escopo(estado: EstadoBlua) -> dict:
    """Responde quando a intent está fora do escopo cardiovascular."""
    resposta = (
        "Sou especializado em saúde cardiovascular e sistema circulatório — "
        "esse tema está fora do meu escopo de atuação. "
        "Para outros assuntos de saúde, recomendo contatar o canal de clínica "
        "geral da Care Plus ou seu médico de referência. "
        "Posso te ajudar com algo relacionado ao seu coração ou pressão arterial?"
        "\n\n⚕️ *Este assistente não substitui avaliação médica. "
        "Em emergência, ligue 192 (SAMU).*"
    )
    return {
        "resposta_agente": resposta,
        "agente_ativo": "fora_escopo",
        "tools_chamadas": [],
    }


def no_safety(estado: EstadoBlua) -> dict:
    """Valida a resposta do agente antes de entregar ao usuário."""
    resultado = agente_safety(
        mensagem_usuario=estado["mensagem_usuario"],
        resposta_agente=estado["resposta_agente"],
        intent=estado.get("intent_classificada", "checkup"),
    )

    if resultado["flags"]:
        print(f"[graph] Safety flags: {resultado['flags']}")

    return {
        "resposta_validada": resultado["resposta"],
        "flags_safety": resultado["flags"],
        "aprovado": resultado["aprovado"],
    }


def no_saida(estado: EstadoBlua) -> dict:
    """
    Finaliza o turno, atualiza histórico e registra no audit log.
    """
    resposta_final = estado["resposta_validada"]

    # Atualizar histórico com o turno atual
    novo_historico = [
        {"role": "user", "content": estado["mensagem_usuario"]},
        {"role": "assistant", "content": resposta_final},
    ]

    # Registrar no audit log
    registrar_turno(
        mensagem_usuario=estado["mensagem_usuario"],
        resposta_agente=resposta_final,
        agente_ativo=estado.get("agente_ativo", "desconhecido"),
        intent=estado.get("intent_classificada", "desconhecido"),
        tools_chamadas=estado.get("tools_chamadas", []),
        flags_safety=estado.get("flags_safety", []),
        beneficiario_id=estado.get("beneficiario_id", "BENEF-001"),
    )

    return {
        "resposta_final": resposta_final,
        "historico": novo_historico,
    }

# Roteamento condicional

def decidir_agente(estado: EstadoBlua) -> str:
    """
    Decide qual nó acionar com base na intent classificada.
    Retorna o nome do próximo nó.
    """
    intent = estado.get("intent_classificada", "checkup")

    mapa = {
        "checkup": "checkup",
        "triagem": "triagem",
        "suporte": "suporte",
        "fora_de_escopo": "fora_escopo",
    }

    return mapa.get(intent, "checkup")


# Construção do grafo

def construir_grafo() -> StateGraph:
    """
    Constrói e compila o StateGraph do BluaDiagnostics.

    Retorna grafo compilado com MemorySaver para
    persistência de estado entre turnos (memória multi-turno).
    """
    builder = StateGraph(EstadoBlua)

    # Adicionar nós
    builder.add_node("roteador", no_roteador)
    builder.add_node("checkup", no_checkup)
    builder.add_node("triagem", no_triagem)
    builder.add_node("suporte", no_suporte)
    builder.add_node("fora_escopo", no_fora_escopo)
    builder.add_node("safety", no_safety)
    builder.add_node("saida", no_saida)

    # Ponto de entrada
    builder.set_entry_point("roteador")

    # Roteamento condicional após classificação de intent
    builder.add_conditional_edges(
        "roteador",
        decidir_agente,
        {
            "checkup": "checkup",
            "triagem": "triagem",
            "suporte": "suporte",
            "fora_escopo": "fora_escopo",
        }
    )

    # Todos os agentes vão para safety
    builder.add_edge("checkup", "safety")
    builder.add_edge("triagem", "safety")
    builder.add_edge("suporte", "safety")
    builder.add_edge("fora_escopo", "safety")

    # Safety vai para saída
    builder.add_edge("safety", "saida")

    # Saída encerra o grafo
    builder.add_edge("saida", END)

    # Compilar com memória para multi-turno
    memoria = MemorySaver()
    grafo = builder.compile(checkpointer=memoria)

    print("[graph] Grafo BluaDiagnostics compilado com sucesso.")
    return grafo


# Função de execução de turno

def executar_turno(
    grafo: StateGraph,
    mensagem_usuario: str,
    thread_id: str,
    beneficiario_id: str = "BENEF-001",
    historico: list[dict] | None = None,
) -> dict:
    """
    Executa um turno de conversa no grafo.

    Args:
        grafo: Grafo compilado pelo construir_grafo().
        mensagem_usuario: Mensagem atual do usuário.
        thread_id: ID único da sessão — preserva memória entre turnos.
        beneficiario_id: ID do beneficiário mockado.
        historico: Histórico externo opcional (para compatibilidade com CLI).

    Returns:
        Estado final do grafo após o turno.
    """
    estado_inicial = {
        "mensagem_usuario": mensagem_usuario,
        "beneficiario_id": beneficiario_id,
        "historico": historico or [],
        "intent_classificada": "",
        "confianca_intent": 0.0,
        "resposta_agente": "",
        "agente_ativo": "",
        "tools_chamadas": [],
        "resposta_validada": "",
        "flags_safety": [],
        "aprovado": True,
        "resposta_final": "",
    }

    config = {"configurable": {"thread_id": thread_id}}

    estado_final = grafo.invoke(estado_inicial, config=config)
    return estado_final