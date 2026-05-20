# Modos de deployment do BluaDiagnostics

> O sistema suporta dois modos de deployment desde a Sprint 1, com troca
> de backend feita por flag (`backend="dashscope"` vs `backend="ollama"`).
> Nenhuma alteração de código consumidor é necessária.
>
> **No Google Colab**, apenas a Configuração A (DashScope) é viável — o
> runtime do Colab não roda servidor Ollama por padrão. A Configuração B
> existe para clientes corporativos com hardware próprio (descrita aqui
> para fins de roadmap).

## Configuração A — Cloud DashScope (padrão Colab)

**Quando usar**: PoC no Colab, ambiente de homologação, primeira fase de
produção, ambientes em que o trade-off latência/custo é favorável e os
dados em trânsito estão dentro dos termos contratuais com a Alibaba Cloud.

**Stack**:
- Modelo: `qwen-plus` (recomendado, fixado na família Qwen) ou `qwen-max` para casos críticos.
- Endpoint: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`.
- SDK: `openai` Python (DashScope é OpenAI-compatible).

**Setup mínimo no Colab**:
1. Abra `notebooks/sprint1_poc.ipynb`.
2. Adicione `DASHSCOPE_API_KEY` em Colab Secrets (🔑) com Notebook access.
3. Rode `Runtime → Run all`.

**Setup mínimo em ambiente local (alternativo)**:
```bash
export DASHSCOPE_API_KEY=...   # obtenha em bailian.console.alibabacloud.com
pip install -r requirements.txt
python -m evals.run_evals --backend dashscope
```

**Vantagens**:
- Zero infraestrutura para gerir.
- Escalonamento automático.
- Acesso a modelos de ponta (Qwen plus/max) sem custo de hardware.
- Hybrid thinking mode totalmente suportado.

**Desvantagens**:
- Tráfego de dados clínicos sai do território nacional — exige análise
  jurídica para LGPD em alguns casos.
- Latência variável dependendo da região.
- Custo por token, embora competitivo.

## Configuração B — On-prem com Ollama (fora do Colab)

**Quando usar**: clientes corporativos da Care Plus que exigem
isolamento total dos dados, ambiente de contingência (caso DashScope
fique indisponível), e ambientes onde o custo de inferência variável é
proibitivo. **Não funciona no Colab gratuito** porque exige um servidor
Ollama persistente na máquina hospedeira.

**Stack**:
- Modelo: `qwen:9b` quantizado pelo Ollama (Q4_K_M) — ~5,5 GB.
- Endpoint: `http://localhost:11434/v1` (OpenAI-compatible).
- Hardware mínimo: GPU com 12 GB de VRAM (ex.: RTX 3060 12GB,
  L4, A10).
- Hardware recomendado: 24 GB de VRAM (RTX 3090, RTX 4090, A6000)
  para variante MoE 35B-A3B.

**Setup mínimo**:
```bash
ollama pull qwen:9b
ollama create blua-qwen -f ollama/Modelfile
export OLLAMA_BASE_URL=http://localhost:11434/v1
export QWEN_OLLAMA_MODEL=blua-qwen
python -m evals.run_evals --backend ollama
```

**Vantagens**:
- Dados nunca saem da rede local.
- Latência previsível (depende só do hardware).
- Custo fixo de hardware, sem variação por uso.
- Possibilidade de fine-tuning local para protocolos Care Plus
  específicos (em sprints futuras).

**Desvantagens**:
- Capacidade limitada — modelo 9B fica abaixo do 35B-A3B em raciocínio
  sutil.
- Hybrid thinking mode suportado parcialmente — em alguns builds o
  toggle precisa ser feito via prompt em vez de parâmetro de API.
- Necessidade de manter GPU saudável e atualizada.
- Function calling exige Ollama ≥ 0.3.0.

## Como o BluaDiagnostics troca entre as duas configurações

Toda a lógica vive no `src/llm/qwen_client.py`. O parâmetro `backend` da
função `chat()` define o endpoint e o modelo. Os agentes em
`src/agents/` recebem `backend` como parâmetro e propagam.

```python
# Cloud
saida = chat(messages=msgs, backend="dashscope")

# On-prem
saida = chat(messages=msgs, backend="ollama")
```

O grafo LangGraph (`src/graph.py`) propaga o backend via `EstadoBlua`,
ou seja: defina uma vez ao iniciar o turno e todos os nós obedecem.

## Roadmap de deployment

| Sprint | Marco |
|---|---|
| Sprint 1 (atual) | PoC entregue como notebook Colab usando DashScope; simulação on-prem com Ollama documentada |
| Sprint 2 | Homologação na Care Plus em ambiente isolado, ainda DashScope |
| Sprint 3 | Piloto restrito com 200 beneficiários — Configuração A |
| Sprint 4 | Decisão sobre Configuração B definitiva: GPU dedicada ou cloud privada |
| Sprint 5 | Rollout completo, com ambos backends em produção (A para volume, B para clientes corporativos sensíveis) |

## Observabilidade comum

Independentemente do backend, o `audit_log.py` produz JSON estruturado
com `structlog` em `/logs/`. Em produção, esse fluxo é encaminhado para
um agregador (ELK, Datadog, ou equivalente Care Plus) para auditoria
LGPD, monitoramento de red flags e análise de qualidade.

## Critérios de troca emergencial

O time de plataforma Care Plus pode redirecionar 100% do tráfego ao
backend secundário em até 5 minutos quando:

- Latência p95 do backend principal ultrapassar 8 s por 10 minutos.
- Taxa de erro 5xx ultrapassar 5%.
- Falha de pipeline de auditoria comprometer a captura de logs LGPD.
- Decisão jurídica/regulatória exigir interrupção do tráfego externo.
