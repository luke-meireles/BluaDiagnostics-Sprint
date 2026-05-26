"""
Pacote de agentes especializados do BluaDiagnostics.

Atualizado Sprint 2:
- Exporta agente_prescricao (5º especialista)
- Mantém compat com 'rotear' (renomeado conceitualmente para supervisor)
- Adiciona 'supervisionar' com lógica estatal
"""

from .router import rotear, supervisionar
from .checkup import agente_checkup
from .triagem import agente_triagem
from .suporte import agente_suporte_clinico
from .prescricao import agente_prescricao
from .safety import agente_safety

__all__ = [
    "rotear",
    "supervisionar",
    "agente_checkup",
    "agente_triagem",
    "agente_suporte_clinico",
    "agente_prescricao",
    "agente_safety",
]
