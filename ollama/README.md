# Ollama — Modo Local (LGPD)

> Modo de execução on-premise do BluaDiagnostics. Justifica narrativa LGPD
> e permite operação sem chamadas a serviços externos.

## Pré-requisitos

- **Ollama ≥ 0.3.0** ⚠️ Versões anteriores **NÃO suportam** function calling.
  Verificar: `ollama --version`
- Modelo: `qwen2.5:14b-instruct` (recomendado) ou `qwen2.5:7b-instruct` (CPU)
- Memória: 16GB RAM para 14b, 8GB para 7b

## Instalação

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows: baixar instalador em https://ollama.com/download

# Verificar versão (precisa ser >= 0.3.0)
ollama --version
```

## Baixar o modelo

```bash
# Modelo recomendado (9GB)
ollama pull qwen2.5:14b-instruct

# Alternativa para máquinas menos potentes (4.7GB)
ollama pull qwen2.5:7b-instruct
```

## Configurar BluaDiagnostics

Editar `.env`:

```bash
LLM_BACKEND=ollama
QWEN_OLLAMA_MODEL=qwen2.5:14b-instruct
OLLAMA_BASE_URL=http://localhost:11434
```

Ou criar arquivo `Modelfile` customizado (variante "blua-qwen"):

```dockerfile
FROM qwen2.5:14b-instruct

PARAMETER temperature 0.3
PARAMETER top_p 0.9

SYSTEM """
Você é o BluaDiagnostics — assistente cardiovascular Care Plus.
Especialização cardiovascular estrita. Nunca emite diagnóstico definitivo.
"""
```

Criar a variante:
```bash
ollama create blua-qwen -f ollama/Modelfile
```

E em `.env`: `QWEN_OLLAMA_MODEL=blua-qwen`

## Executar

```bash
# Rodar Ollama em background (Linux)
ollama serve &

# Em outro terminal, rodar BluaDiagnostics
python app/dash_app.py
```

## Latência esperada

| Hardware | Modelo | Latência por turno |
|---|---|---|
| GPU RTX 3060+ | qwen2.5:14b | ~3-5s |
| CPU moderno (i7+) | qwen2.5:14b | ~10-15s |
| CPU básico | qwen2.5:7b | ~12-20s |
| Mac M1/M2/M3 | qwen2.5:14b | ~5-8s |

## Narrativa LGPD para o vídeo

> "Em produção real Care Plus, este sistema rodaria com Ollama on-premise:
> nenhum dado clínico de paciente sai da máquina, atendendo plenamente os
> Artigos 7º, 11 e 18 da LGPD. A demonstração em DashScope é apenas para
> velocidade de iteração acadêmica."

## Troubleshooting

**Erro: "tool_choice not supported"**
→ Ollama < 0.3.0. Atualize com `curl -fsSL https://ollama.com/install.sh | sh`.

**Resposta muito lenta**
→ Trocar para qwen2.5:7b (mais leve) ou liberar GPU.

**Modelo não responde**
→ Verificar se Ollama está rodando: `ollama list`. Reiniciar: `ollama serve`.
