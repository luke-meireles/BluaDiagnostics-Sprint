# Configuração on-prem do BluaDiagnostics com Ollama

> **Importante**: o projeto BluaDiagnostics foi escrito **para o Google
> Colab**. Esta pasta documenta o modo on-prem (Ollama) apenas como
> **alternativa fora do Colab** — clientes corporativos com isolamento
> total ou ambientes de contingência. **Não funciona no Colab gratuito**
> porque o runtime não suporta servidor Ollama persistente.

Esta pasta contém o `Modelfile` que materializa a Configuração B (on-prem)
do BluaDiagnostics: o mesmo Qwen 9B servido localmente via
[Ollama](https://ollama.com), com o system prompt principal embutido.

## Por que on-prem?

A Care Plus opera sob LGPD e atende beneficiários cujo histórico clínico é
dado sensível. Em ambientes que exigem **isolamento total** (servidor da
operadora, datacenter brasileiro, sem tráfego externo), o Ollama serve a
mesma família Qwen sem chamadas a APIs externas. Trade-off: latência maior
e necessidade de GPU local. Mais detalhes em [`/docs/deployment_modes.md`](../docs/deployment_modes.md).

## Pré-requisitos

- Ollama instalado (versão ≥ 0.3.0).
- GPU com pelo menos 12 GB de VRAM recomendada para qwen:9b. Em CPU,
  funciona, porém com latência elevada.

## Setup

```bash
# 1. Baixe o modelo base
ollama pull qwen:9b

# 2. Crie a variante BluaDiagnostics com o system prompt embutido
ollama create blua-qwen -f Modelfile

# 3. Teste interativo
ollama run blua-qwen "Olá, estou com dor de cabeça leve há dois dias."
```

## Apontando o BluaDiagnostics ao Ollama

Defina as variáveis de ambiente:

```bash
export OLLAMA_BASE_URL=http://localhost:11434/v1
export QWEN_OLLAMA_MODEL=blua-qwen   # ou qwen:9b se preferir
```

E no código consumidor, chame `chat(..., backend="ollama")` ou use
`OllamaClient()` em vez do `QwenClient()`.

## Limitações conhecidas

- O Ollama local não suporta `enable_thinking=True` da mesma forma que a
  DashScope. Para a Sprint 1, o agente de Triagem cai em modo non-thinking
  quando o backend é Ollama — o impacto é menor porque o RAG e a heurística
  determinística de risco já fazem o trabalho pesado.
- Function calling em modo OpenAI-compatible no Ollama precisa de versão
  recente. Em caso de erro, atualizar o Ollama e reverificar.

## Como verificar a integração

```bash
python -c "from src.llm.qwen_client import chat; print(chat([{'role':'user','content':'oi'}], backend='ollama'))"
```

Se retornar dicionário com `content` preenchido, está tudo certo.
