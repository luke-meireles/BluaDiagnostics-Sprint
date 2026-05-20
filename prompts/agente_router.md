# Agente Roteador (Intent Classification)

## 1. Visão Geral

O **Agente Roteador** é um componente central da arquitetura do sistema *BluaDiagnostics*, responsável por realizar a **classificação de intenção do usuário (Intent Classification)** e direcionar a conversa para o agente apropriado.

Ele atua como o **primeiro ponto de decisão do pipeline conversacional**, garantindo que cada requisição do usuário seja encaminhada corretamente para módulos especializados, como check-up, triagem ou suporte clínico.

O agente opera em modo de baixa latência (`thinking=OFF`), priorizando rapidez e eficiência na decisão.

---

## 2. Objetivo do Agente

O objetivo principal do roteador é:

- Classificar a intenção da mensagem do usuário
- Determinar qual agente deve ser acionado
- Garantir consistência no fluxo conversacional
- Reduzir carga desnecessária nos agentes especializados

Ele funciona como um **classificador leve e determinístico**, essencial para escalabilidade do sistema.

---

## 3. Arquitetura Geral

O agente segue uma arquitetura baseada em LLM com saída estruturada.

### Componentes principais:

- Cliente LLM (`chat` via Qwen)
- Formatter de mensagens (`formatar_mensagens`)
- System Prompt com regras rígidas de saída
- Parser JSON de resposta
- Sistema de fallback seguro

---

## 4. Categorias de Intenção

O roteador classifica todas as mensagens em quatro categorias principais:

### 4.1 checkup
Usuário deseja realizar um check-up cardiovascular ou analisar sinais vitais.

Exemplos:
- Solicitação de check-up
- Envio de batimentos cardíacos
- Análise preventiva

---

### 4.2 triagem
Usuário relata sintomas agudos potencialmente críticos.

Exemplos:
- Dor no peito
- Falta de ar
- Tontura
- Palpitações intensas

Esta categoria tem prioridade clínica elevada e geralmente encaminha para fluxos de urgência.

---

### 4.3 suporte
Usuário busca informações sobre:

- Interações medicamentosas
- Dúvidas sobre medicamentos
- Histórico clínico

---

### 4.4 fora_de_escopo
Mensagens que não pertencem ao domínio cardiovascular.

Exemplos:
- Perguntas gerais de outras áreas médicas
- Assuntos não relacionados à saúde cardiovascular

---

## 5. System Prompt e Regras de Saída

O comportamento do modelo é rigidamente controlado por um System Prompt estruturado.

### 5.1 Regras principais

- Retornar **apenas JSON válido**
- Não incluir explicações ou texto adicional
- Seguir estritamente as categorias definidas

### 5.2 Formato obrigatório de saída

```json
{"intent": "checkup"|"triagem"|"suporte"|"fora_de_escopo", "confianca": 0.0-1.0}