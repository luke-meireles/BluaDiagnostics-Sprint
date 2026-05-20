"""
Exporta todas as tools para uso nos agentes
"""

from .historico import consultar_historico_paciente
from .interacoes import verificar_interacoes_medicamentosas
from .agendamento import agendar_teleconsulta
from .ritmo import analisar_ritmo_cardiaco
from .wearable import consultar_sinais_vitais_wearable

__all__ = [
    "consultar_historico_paciente",
    "verificar_interacoes_medicamentosas",
    "agendar_teleconsulta",
    "analisar_ritmo_cardiaco",
    "consultar_sinais_vitais_wearable"
]