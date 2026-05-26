"""
Pre-Safety Layer
Filtro rápido determinístico ANTES do supervisor LLM.

Bloqueia padrões óbvios de jailbreak e fora-de-escopo via regex,
economizando tokens do LLM em casos triviais e fornecendo defesa
em profundidade junto com a safety pós-resposta.

Saídas possíveis:
- {"bloqueado": False, ...}  → segue para supervisor
- {"bloqueado": True, "motivo": "jailbreak", "resposta": str}
- {"bloqueado": True, "motivo": "fora_de_escopo", "resposta": str}
"""

from __future__ import annotations

import re


# Padrões de jailbreak óbvios — case insensitive
# Lista conservadora para evitar falsos positivos com perguntas legítimas
_PADROES_JAILBREAK = [
    r"\bignore (?:as |todas as |suas )?instru[cç][oõ]es",
    r"\besque[cç]a (?:as |todas as |suas )?instru[cç][oõ]es",
    r"\bdeveloper mode\b",
    r"\bact as\b",
    r"\batue como\b(?!.*cardio)",         # "atue como cardiologista" não é jailbreak
    r"\bfinja (?:que|ser)\b",
    r"\bpretend (?:to be|you are)\b",
    r"\bdo anything now\b",
    r"\bdan mode\b",
    r"\bsem (?:restri[cç][oõ]es|filtros|limites)\b",
    r"\bvoc[eê] (?:agora )?[ée] (?:um |uma )?(?:hacker|jailbreak)\b",
    r"\bbypass(?:e|ar)? (?:safety|guardrails|filtros)\b",
    r"\bjailbreak\b",
    r"\bprompt injection\b",
]

# Tópicos óbvios fora do escopo cardiovascular
# Padrão: a palavra-chave em contexto que sugira pedido de orientação clínica
_PADROES_FORA_ESCOPO = [
    # Outras especialidades médicas
    r"\b(?:diabetes|glicemia|insulina|hemoglobina glicada)\b(?!.*card[ií]ac)",
    r"\b(?:dermatite|psor[ií]ase|melanoma|man[cç]ha na pele)\b",
    r"\b(?:enxaqueca|cefaleia|dor de cabe[cç]a (?:cr[oô]nica|forte))\b(?!.*pressão|hipertens)",
    r"\b(?:ans?iedade|depress[aã]o|p[aâ]nico|ins[oô]nia)\b(?!.*card[ií]ac)",
    r"\b(?:gastrite|refluxo|úlcera|h[eé]rnia)\b",
    r"\b(?:dor (?:de )?dente|c[aá]rie|gengivite)\b",
    r"\b(?:gravidez|menstrua[cç][aã]o|anticoncepcional)\b(?!.*pr[eé][- ]ecl[aâ]mpsia|risco card|periparto)",
    # Não-clínico
    r"\b(?:programa[cç][aã]o|c[oó]digo|python|javascript|html|css)\b",
    r"\bcomo (?:fazer|criar|escrever|codar|programar)\b",
    r"\b(?:elei[cç][aã]o|presidente|pol[ií]tic[ao])\b",
    r"\b(?:matem[aá]tica|equa[cç][aã]o|c[aá]lculo|integral)\b",
    r"\b(?:receita (?:de )?(?:bolo|comida|culin[aá]ria))\b",
    r"\b(?:traduz|tradu[cç][aã]o|english|inglês)\b(?!.*card)",
]

_REGEX_JAILBREAK = re.compile("|".join(_PADROES_JAILBREAK), re.IGNORECASE)
_REGEX_FORA_ESCOPO = re.compile("|".join(_PADROES_FORA_ESCOPO), re.IGNORECASE)


_RESPOSTA_JAILBREAK = (
    "Não vou seguir instruções que tentem alterar meu comportamento. "
    "Sou um assistente especializado em saúde cardiovascular da Care Plus "
    "e mantenho minhas diretrizes clínicas sempre ativas.\n\n"
    "Posso te ajudar com algo relacionado ao seu coração ou pressão arterial?\n\n"
    "⚕️ *Este assistente não substitui avaliação médica. "
    "Em emergência, ligue 192 (SAMU).*"
)

_RESPOSTA_FORA_ESCOPO = (
    "Sou especializado em saúde cardiovascular e sistema circulatório — "
    "esse tema está fora do meu escopo de atuação.\n\n"
    "Para outros assuntos de saúde, recomendo contatar o canal de clínica "
    "geral da Care Plus pelo app Blua ou seu médico de referência.\n\n"
    "Posso te ajudar com algo relacionado ao seu coração ou pressão arterial?\n\n"
    "⚕️ *Este assistente não substitui avaliação médica. "
    "Em emergência, ligue 192 (SAMU).*"
)


def pre_safety_check(mensagem: str) -> dict:
    """
    Verifica a mensagem do usuário ANTES de qualquer chamada de LLM.

    Args:
        mensagem: Mensagem atual do usuário.

    Returns:
        Dicionário com:
        - bloqueado (bool): True se a mensagem deve ser bloqueada
        - motivo (str|None): 'jailbreak' | 'fora_de_escopo' | None
        - resposta (str|None): resposta padrão se bloqueado
        - padrao_detectado (str|None): padrão regex que casou (para audit log)
    """
    if not mensagem or not mensagem.strip():
        return {
            "bloqueado": False,
            "motivo": None,
            "resposta": None,
            "padrao_detectado": None,
        }

    # 1. Jailbreak — prioridade máxima, bloqueia antes de qualquer coisa
    match_jb = _REGEX_JAILBREAK.search(mensagem)
    if match_jb:
        return {
            "bloqueado": True,
            "motivo": "jailbreak",
            "resposta": _RESPOSTA_JAILBREAK,
            "padrao_detectado": match_jb.group(0),
        }

    # 2. Fora de escopo cardiovascular
    match_oos = _REGEX_FORA_ESCOPO.search(mensagem)
    if match_oos:
        return {
            "bloqueado": True,
            "motivo": "fora_de_escopo",
            "resposta": _RESPOSTA_FORA_ESCOPO,
            "padrao_detectado": match_oos.group(0),
        }

    # 3. Passa para o supervisor
    return {
        "bloqueado": False,
        "motivo": None,
        "resposta": None,
        "padrao_detectado": None,
    }
