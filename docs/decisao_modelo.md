# Decisão de modelo — Qwen vs Llama 3.3 70B

> Documento de Architectural Decision Record (ADR) para a Sprint 1 do
> BluaDiagnostics. Justifica a escolha do Qwen sobre o Llama 3.3 70B,
> únicos candidatos avaliados nesta sprint conforme escopo definido.

## Contexto

A operadora Care Plus precisa de um LLM que sustente o BluaDiagnostics em
produção. O sistema é clínico, opera em PT-BR, lida com dados sensíveis
sob LGPD, exige function calling robusto e precisa rodar tanto em nuvem
(DashScope) quanto em ambiente on-premise (Ollama). Avaliamos dois modelos
abertos competitivos: **Qwen** (família Alibaba) e **Llama 3.3 70B**
(Meta).

## Critérios de avaliação

1. Instruction following (capacidade de seguir guardrails clínicos).
2. Qualidade de PT-BR clínico nativo.
3. Function calling (tool use) confiável.
4. Hybrid thinking mode (raciocínio sob demanda sem trocar de modelo).
5. Licença comercial favorável.
6. Variantes de tamanho que permitam on-prem viável.
7. Ecossistema de frameworks de agente.

## Tabela comparativa

| Critério | Qwen (escolhido) | Llama 3.3 70B |
|---|---|---|
| Lançamento | 2025–2026, atualizações frequentes | dez/2024 |
| PT-BR nativo | treinado em 201 idiomas com qualidade clínica | bom em PT-BR mas sem foco médico |
| Function calling | nativo, JSON Schema OpenAI-compatible | suportado via templates, com mais reescrita |
| IFBench (instruction follow) | 76,5 (resultado público) | ~71 |
| Licença | Apache 2.0 — comercial liberado | Llama Community License com restrições (>700M MAU, branding etc.) |
| Hybrid thinking mode | sim, toggle por chamada via `enable_thinking` | não — raciocínio é sempre uniforme |
| Janela de contexto | até 1M tokens em variantes especializadas | 128K |
| Arquitetura | dense + variantes MoE (35B-A3B ativa apenas 3B) | dense 70B, custo de inferência maior |
| Custo cloud | DashScope International, preço competitivo | requer hosts próprios ou parceiros |
| On-prem | Ollama, vLLM, llama.cpp — quantizações <16GB | Ollama, vLLM — exige >40GB de VRAM em FP16 |
| Frameworks de agente | `qwen-agent` oficial + LangGraph | LangGraph, LangChain |

## Cinco motivos centrais para Qwen

### 1. Instruction following (IFBench 76,5)

O Qwen lidera em benchmarks de seguimento de instrução. Em saúde
digital, a regra inegociável precisa ser respeitada **incondicionalmente**.
Diferenças de 5 pontos no IFBench se traduzem em centenas de violações
evitadas por mês na escala da Care Plus (600k+ beneficiários).

### 2. PT-BR nativo de qualidade clínica

A família Qwen foi treinada em 201 idiomas com cobertura ampla de PT-BR,
incluindo termos clínicos. Em testes informais com bulas e protocolos de
triagem, mantém terminologia consistente sem alucinar termos em espanhol
ou português europeu — problema recorrente quando se usa Llama em PT-BR.

### 3. Hybrid thinking mode

O toggle `enable_thinking` permite que o Roteador opere em modo rápido
(latência baixa, sem `<think>`) e o Triagem opere em modo deliberativo
sem trocar de modelo. Isso reduz custo operacional e simplifica a stack.
O Llama 3.3 não tem essa flexibilidade nativa — exige modelos separados
ou prompting custoso.

### 4. Licença Apache 2.0

A Care Plus é uma operadora comercial. Apache 2.0 é a licença mais
permissiva entre LLMs abertos competitivos: liberdade total de uso,
modificação e redistribuição, inclusive como serviço. A Llama Community
License impõe restrições que tornam o programa de white-label do app
Blua arriscado juridicamente.

### 5. Eficiência via MoE e variantes leves

A variante Qwen 35B-A3B (Mixture of Experts) ativa apenas ~3B
parâmetros em inferência, oferecendo qualidade próxima de modelos densos
muito maiores com fração do custo. Para servidor on-prem da Care Plus,
isso significa dimensionar GPU para 24GB em vez de 80GB, viabilizando
hardware existente.

## Riscos e mitigações

- **Dependência de fornecedor (Alibaba)**: mitigado pela disponibilidade
  do modelo via Ollama, llama.cpp e weights em Hugging Face.
- **Cobertura clínica imperfeita**: mitigado pelo RAG com knowledge base
  curada (7 documentos em PT-BR com red flags, bulas, políticas).
- **Possível degradação em jailbreaks sofisticados**: mitigado pelo
  Safety Layer que faz uma segunda chamada de auditoria e pode reprovar
  respostas que escapem do guardrail principal.

## Decisão

Adotamos **Qwen** como modelo principal do BluaDiagnostics, com
duas configurações homologadas:

- **Configuração A (cloud)**: `qwen-plus` via DashScope International (família Qwen fixada),
  para o ambiente de homologação e a primeira fase de produção.
- **Configuração B (on-prem)**: `qwen:9b` via Ollama, para clientes
  corporativos com requisitos de isolamento total ou para o ambiente de
  contingência.

## Revisão

Esta decisão será revisitada na Sprint 4 ou quando:

- Surgir uma versão maior do Llama (Llama 4) com IFBench superior e
  licença mais flexível.
- Aparecer um modelo brasileiro especializado em saúde (ex.: BR-LLM
  cardiometabólico) que valha o trade-off de cobertura por especialização.
- Mudar o panorama regulatório ANS/ANPD que torne on-prem mandatório.
