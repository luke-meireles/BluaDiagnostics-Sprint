# BluaDiagnostics — Care Plus

> Assistente cardiovascular digital · LangGraph multi-agente · RAG · LGPD-ready
> **Sprint 2** — Sistema completo evoluindo a PoC da Sprint 1

[![Sprint](https://img.shields.io/badge/Sprint-2-blue)](docs/relatorio_final.md)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## O que é

BluaDiagnostics é um sub-app do **Blua** (plataforma da operadora Care Plus) que automatiza dois fluxos clínicos cardiovasculares:

1. **Check-up cardiovascular conversacional** — coleta sinais vitais, analisa wearable, agenda teleconsulta
2. **Rascunho de prescrição pós-teleconsulta com revisão médica humana (HITL)**

Especialização cardiovascular **estrita** — pedidos fora do escopo são polidamente recusados e redirecionados.

---

## Arquitetura

**10 nós LangGraph** (vs 7 na Sprint 1):

```
Usuário → Pre-Safety → Supervisor (estatal)
            ↓
   ┌────────┼─────────┬─────────┬──────────┬──────────┐
   ↓        ↓         ↓         ↓          ↓          ↓
Checkup  Triagem   Suporte  Prescrição  Escalada  ForaEscopo
           +Rerank    +RAG    +HITL     +SAMU
   └────────┴─────────┴─────────┴──────────┴──────────┘
                        ↓
                Safety dupla camada
                        ↓
            Saída (audit + truncagem)
                        ↓
                     Usuário
```

5 agentes especializados + 2 nós de proteção + 1 nó determinístico de escalada.

Ver `docs/relatorio_final.md` para diagrama Mermaid completo e justificativa de cada decisão.

---

## Modos de execução

O BluaDiagnostics é **tri-modal**:

| Modo | Quando | Custo | Privacidade |
|---|---|---|---|
| **DashScope** (cloud, default) | Demos rápidas, evals | ~$0.001/turno | Externa |
| **Ollama** (local) | Produção LGPD-ready | $0 | On-prem |
| **Híbrido** | Alternância | — | — |

Troca de modo via uma linha no `.env`:

```bash
LLM_BACKEND=dashscope    # ou: ollama
```

---

## Quickstart

```bash
# 1. Clonar e instalar
git clone <repo>
cd BluaDiagnostics
pip install -r requirements.txt

# 2. Configurar
cp .env.example .env
# Editar .env: DASHSCOPE_API_KEY=sk-xxx

# 3. Popular ChromaDB (uma vez, ~85 chunks de 11 documentos)
bash scripts/index_kb.sh

# 4. Iniciar interface Dash (principal)
python app/dash_app.py
# Abre em http://localhost:8050

# Alternativa: Streamlit (fallback)
streamlit run app/streamlit_app.py

# 5. Rodar evals (gera sprint2_results.json + gráficos)
python -m evals.run_evals_sprint2

# 6. Rodar testes
pytest tests/ -v
```

---

## Sprint 2 — O que mudou

### Funcionalidades

| Área | Sprint 1 | Sprint 2 |
|---|---|---|
| **Interface** | CLI + Notebook | **Dash** + Streamlit fallback |
| **Agentes** | 4 | **5** (+ Prescrição) |
| **Nós LangGraph** | 7 | **10** (+ pre_safety, prescricao, escalada_humana) |
| **Supervisor** | Classificador estático | **Estatal** (força triagem se RED_FLAG persistir) |
| **Safety** | Heurística regex | **Dupla camada** (heurística + LLM auditor) |
| **RAG** | Similarity search | **MMR + Auto-RAG + Reranker + filtros por categoria** |
| **Memória** | Cumula indefinidamente | **Summarize-and-replace** após 6 turnos |
| **Confidence scoring** | — | **Numérico** baseado em RAG + intent + tools |
| **HITL** | — | **Síncrono** via `interrupt_before` |
| **Observabilidade** | Audit log local | **+ LangSmith** integrado |
| **Evals** | 22 casos | **32 casos** (+ apresentações atípicas + prescrição) |
| **Testes** | — | **4 arquivos pytest** |

### Apresentações atípicas (Patch 2)

Knowledge base expandida com:
- `cardiologia_gravidez_pre_eclampsia.md` (cardiomiopatia periparto, pré-eclâmpsia)
- `cardiologia_jovens_atletas.md` (CMH, síncope em jovens, síndromes de pré-excitação)

Casos de eval cobrindo: Síndrome de Takotsubo, IAM atípico em diabético, dissecção aórtica, TEP em jovem.

---

## Estrutura

```
src/
├── prompts.py                # loader único de prompts .md
├── graph.py                  # LangGraph 10 nós (refatorado Sprint 2)
├── agents/
│   ├── router.py             # supervisor estatal
│   ├── pre_safety.py         # NOVO — regex jailbreak/OOS
│   ├── checkup.py            # refatorado — RAG detalhado
│   ├── triagem.py            # refatorado — Reranker ATIVO
│   ├── suporte.py            # refatorado
│   ├── prescricao.py         # NOVO — 5º especialista
│   ├── escalada_humana.py    # NOVO — SAMU/FAST
│   └── safety.py             # refatorado — dupla camada
├── rag/
│   ├── indexer.py            # + metadado categoria
│   ├── retriever.py          # + MMR + Auto-RAG + filtros
│   └── reranker.py           # ATIVO no Triagem
├── tools/
│   ├── prescricao.py         # NOVO — tag inviolável
│   └── ... (tools Sprint 1)
└── utils/
    └── memoria.py            # NOVO — summarize-and-replace

app/
├── dash_app.py               # interface principal (Sprint 2)
├── streamlit_app.py          # fallback
└── assets/
    ├── style.css             # design system HUD
    ├── blua_custom.css       # customizações Blua
    └── alert.wav             # som red flag

prompts/                      # 6 prompts em Markdown + CHANGELOG
evals/                        # 32 casos + runner + resultados
tests/                        # 4 arquivos pytest
docs/                         # relatório técnico + figuras
knowledge_base/               # 11 documentos cardiovasculares
scripts/                      # index_kb.sh
ollama/                       # Modelfile + README on-prem
```

---

## Observabilidade

Para ativar LangSmith (3 env vars, free tier 5k traces/mês):

```bash
# .env
LANGSMITH_API_KEY=ls__xxx
LANGSMITH_PROJECT=BluaDiagnostics-Sprint2
```

LangGraph instrumenta automaticamente. Traces aninhados visíveis:
`pre_safety → supervisor → rag_retrieve → triagem → tools → safety`.

Para narrativa LGPD em produção, considerar **LangFuse self-hosted** no mesmo perímetro do Ollama.

---

## Demonstração

Vídeo (5 min): **[link YouTube unlisted]**

Roteiro:
- 0:00–0:30 — Arquitetura
- 0:30–1:30 — Happy path Maria (PDF Sprint 2)
- 1:30–2:15 — Red flag → escalada SAMU automática
- 2:15–3:00 — Prescrição com HITL síncrono
- 3:00–3:30 — Jailbreak duplo (pre_safety + safety auditor)
- 3:30–4:00 — Traces LangSmith
- 4:00–4:45 — **Troca para Ollama on-prem ao vivo** (narrativa LGPD)
- 4:45–5:00 — Métricas finais

---

## Equipe

| Nome | RM |
|---|---|
| Lucas Gabriel Alvarenga e Meireles | 567305 |
| Gabriel Augusto da Silva | 567057 |
| Leonardo Kenji Kubo Barboza | 567518 |
| Lucas Koiti Uyeno de Souza | 568128 |
| Lucas Morio Ikeda | 567616 |

---

## Limitações e Roadmap

Modelo de ML real de detecção de arritmias do grupo (de outra disciplina) NÃO está integrado nesta entrega — fica como roadmap. A tool `analisar_ritmo_cardiaco` atual usa regra determinística.

Ver `docs/relatorio_final.md` seções 5 e 6 para limitações e roadmap completos.

---

## Disclaimer

⚕️ Este sistema é um trabalho acadêmico e **não substitui avaliação médica**. Em emergências, ligue **192 (SAMU)**.

Mocks de pacientes são fictícios — não há dados reais de pessoas no repositório.
