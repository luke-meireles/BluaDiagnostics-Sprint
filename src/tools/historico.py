"""
Tool: consultar_historico_paciente
Consulta o histórico clínico cardiovascular do beneficiário por tipo
"""

import json
from pathlib import Path

# Caminho para o mock de perfis clínicos
_MOCK_PATH = Path(__file__).resolve().parents[2] / "data" / "mocks" / "perfis_clinicos.json"


def consultar_historico_paciente(paciente_id: str, tipo: str) -> dict:
    """
    Consulta o histórico cardiovascular do beneficiário por tipo.

    Args:
        paciente_id: ID do beneficiário. Ex: BENEF-001
        tipo: condicoes | medicacoes | consultas | exames | sinais_vitais

    Returns:
        Dicionário com os dados solicitados ou erro se não encontrado.
    """
    tipos_validos = {"condicoes", "medicacoes", "consultas", "exames", "sinais_vitais"}

    if tipo not in tipos_validos:
        return {
            "erro": f"Tipo '{tipo}' inválido.",
            "tipos_validos": list(tipos_validos)
        }

    # Carregar mock
    with open(_MOCK_PATH, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Buscar beneficiário
    beneficiario = next(
        (b for b in dados["beneficiarios"] if b["id"] == paciente_id),
        None
    )

    if not beneficiario:
        return {"erro": f"Beneficiário '{paciente_id}' não encontrado."}

    # Mapear tipo para campo do mock
    mapa = {
        "condicoes": {
            "paciente_id": paciente_id,
            "tipo": "condicoes",
            "dados": {
                "condicoes_ativas": beneficiario.get("condicoes_ativas", []),
                "score_risco_cardiovascular": beneficiario.get("score_risco_cardiovascular"),
                "ultima_atualizacao": beneficiario.get("consultas", {}).get("ultima", {}).get("data")
            }
        },
        "medicacoes": {
            "paciente_id": paciente_id,
            "tipo": "medicacoes",
            "dados": {
                "medicacoes_ativas": beneficiario.get("medicacoes_ativas", []),
                "alergias": beneficiario.get("alergias", []),
            }
        },
        "consultas": {
            "paciente_id": paciente_id,
            "tipo": "consultas",
            "dados": beneficiario.get("consultas", {})
        },
        "exames": {
            "paciente_id": paciente_id,
            "tipo": "exames",
            "dados": {
                "exames_recentes": beneficiario.get("exames_recentes", [])
            }
        },
        "sinais_vitais": {
            "paciente_id": paciente_id,
            "tipo": "sinais_vitais",
            "dados": beneficiario.get("sinais_vitais_ultimo_registro", {})
        },
    }

    return mapa[tipo]