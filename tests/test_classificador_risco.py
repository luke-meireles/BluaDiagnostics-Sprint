"""
Testes unitários para o classificador de risco cardiovascular.
src/tools/classificador_risco.py ou estratificador_cardiovascular.py

Nota: testes adaptados à API atual de `estratificar_dor_toracica` (que
recebe `caracteristicas_dor: list[str]` + `sintomas_associados: list[str]`
em vez dos argumentos escalares `tipo_dor`/`irradiacao`/`sudorese` que o
plano original previa). O retorno usa a chave `nivel` (não `risco`) e
`conduta_recomendada` (não `conduta`).
"""

from __future__ import annotations

import pytest
from src.tools.estratificador_cardiovascular import estratificar_dor_toracica


class TestEstratificacaoDorToracica:
    """HEART score simplificado — testes determinísticos."""

    def test_paciente_alto_risco_classico(self):
        """Idoso, dor opressiva, irradiação, sudorese, múltiplos fatores."""
        resultado = estratificar_dor_toracica(
            idade=68,
            sexo="masculino",
            caracteristicas_dor=["opressiva", "irradiacao_braco_esquerdo"],
            sintomas_associados=["sudorese_fria"],
            fatores_risco=["hipertensao", "diabetes", "tabagismo_ativo", "dislipidemia"],
        )
        assert resultado["nivel"] in {"alto", "critico"}
        assert (
            "SAMU" in resultado["conduta_recomendada"]
            or "emergência" in resultado["conduta_recomendada"]
            or "emergencia" in resultado["conduta_recomendada"]
        )

    def test_paciente_baixo_risco_jovem_pleuritico(self):
        """Jovem, dor pleurítica, sem fatores — não é red flag."""
        resultado = estratificar_dor_toracica(
            idade=22,
            sexo="masculino",
            caracteristicas_dor=["pleuritica"],
            sintomas_associados=[],
            fatores_risco=[],
        )
        assert resultado["nivel"] in {"baixo", "muito_baixo"}

    def test_diabetico_dor_atipica_idade_avancada(self):
        """Diabético idoso com dor atípica — risco intermediário."""
        resultado = estratificar_dor_toracica(
            idade=65,
            sexo="feminino",
            caracteristicas_dor=[],  # atípica = sem descritor de dor clássica
            sintomas_associados=["sudorese_fria"],
            fatores_risco=["diabetes", "hipertensao"],
            grupos_atipicos=["mulher", "diabetico", "idoso_65"],
        )
        # Sintomas atípicos em diabéticos não devem ser descartados
        assert resultado["nivel"] in {"moderado", "alto", "critico"}


class TestRiscoCardiovascularBasico:
    """Caso para o classificador genérico, se diferente do estratificador."""

    def test_pa_emergencia_hipertensiva(self):
        """PA > 180x120 + sintoma neurológico = emergência."""
        try:
            from src.tools.classificador_risco import classificar_risco
        except ImportError:
            pytest.skip("classificador_risco.py não existe — usar estratificador")
            return

        resultado = classificar_risco(
            pa_sistolica=195,
            pa_diastolica=125,
            sintomas=["cefaleia intensa", "visão turva"],
        )
        assert resultado["nivel"] == "alto"

    def test_pa_controlada_normal(self):
        """PA dentro do alvo = baixo risco."""
        try:
            from src.tools.classificador_risco import classificar_risco
        except ImportError:
            pytest.skip("classificador_risco.py não existe — usar estratificador")
            return

        resultado = classificar_risco(
            pa_sistolica=128,
            pa_diastolica=82,
            sintomas=[],
        )
        assert resultado["nivel"] in {"baixo", "muito_baixo"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
