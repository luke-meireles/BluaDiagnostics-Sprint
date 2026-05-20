# Relatório Técnico — Agente de Check-up Cardiovascular

## 1. Visão Geral

O **Agente de Check-up** é um componente de um sistema de diagnóstico assistido por IA desenvolvido para a plataforma *BluaDiagnostics*. Seu objetivo principal é conduzir um **check-up cardiovascular conversacional guiado**, coletando informações clínicas do usuário e integrando dados de histórico médico, sinais vitais e dispositivos wearable.

O agente opera em modo determinístico (`thinking=OFF`), garantindo fluxos controlados e previsíveis, fundamentais para aplicações em saúde.

---

## 2. Objetivo do Agente

O agente tem como finalidade:

- Realizar coleta estruturada de sintomas cardiovasculares
- Consultar histórico clínico do beneficiário
- Analisar ritmo cardíaco com base em dados informados
- Integrar informações de dispositivos wearable
- Sugerir agendamento de teleconsulta quando necessário

O sistema é projetado para **apoio à triagem cardiovascular**, sem substituir avaliação médica profissional.

---

## 3. Arquitetura Geral

O agente é implementado em Python e segue uma arquitetura modular composta por:

- LLM via `chat()` (cliente Qwen)
- Sistema de tools (function calling)
- Módulo RAG (Retrieval-Augmented Generation)
- Pipeline de mensagens conversacionais
- Executor de tools interno

### Fluxo de execução

1. Construção do prompt do sistema
2. Injeção de contexto do beneficiário
3. Recuperação de contexto via RAG
4. Formatação do histórico da conversa
5. Chamada inicial ao modelo
6. Execução de tools (se necessário)
7. Loop iterativo até resposta final

---

## 4. Tools Utilizadas

O agente utiliza quatro ferramentas principais:

### 4.1 consultar_historico_paciente
Permite acessar o histórico clínico do paciente, incluindo condições anteriores e registros relevantes.

### 4.2 analisar_ritmo_cardiaco
Responsável pela análise de padrões de batimentos cardíacos, identificando possíveis irregularidades.

### 4.3 consultar_sinais_vitais_wearable
Integra dados provenientes de dispositivos vestíveis (wearables), como frequência cardíaca e atividade física.

### 4.4 agendar_teleconsulta
Permite o agendamento de consultas médicas remotas quando há necessidade clínica identificada.

---

## 5. Sistema de Prompt (Comportamento do Agente)

O comportamento do agente é controlado por um **System Prompt rígido**, que define:

### 5.1 Escopo de atuação
- Triagem cardiovascular conversacional
- Coleta de sintomas e sinais vitais
- Apoio à decisão de encaminhamento

### 5.2 Restrições médicas
- Proibição de diagnóstico definitivo
- Proibição de prescrição de medicamentos
- Uso de linguagem probabilística (“pode indicar”, “sugere avaliação”)

### 5.3 Diretrizes de interação
- Uma pergunta por vez
- Máximo de 150 palavras por resposta
- Linguagem acessível e acolhedora

### 5.4 Regras de segurança
- Red flags devem aparecer no início da resposta
- Encaminhamento imediato para emergência (SAMU 192) em casos críticos
- Inclusão obrigatória de disclaimer médico

---

## 6. Mecanismo de Execução de Tools

O agente implementa um sistema de **function calling controlado**.

### 6.1 Função `_executar_tool`

Responsável por:

- Mapear nome da tool para função Python correspondente
- Executar a função com argumentos recebidos
- Tratar erros e retornar resposta em JSON

### 6.2 Loop de execução

O agente segue o seguinte padrão:

1. O modelo pode solicitar tools via `tool_calls`
2. Cada tool é executada localmente
3. Resultado é reinserido no contexto da conversa
4. Nova chamada ao modelo é realizada
5. Processo se repete até resposta final

Este mecanismo permite **raciocínio iterativo assistido por ferramentas externas**.

---

## 7. Integração com RAG (Retrieval-Augmented Generation)

O agente utiliza um módulo de recuperação de contexto (`recuperar_contexto`) para enriquecer a resposta com informações relevantes.

Isso permite:

- Melhor contextualização clínica
- Redução de ambiguidades
- Respostas mais informadas com base em dados externos

---

## 8. Estrutura de Dados e Tools Spec

As tools são carregadas dinamicamente a partir de um arquivo:
tools/tools_spec.json

Somente ferramentas relevantes ao check-up são filtradas e incluídas no prompt do modelo, garantindo:

- Redução de ruído
- Melhor precisão no function calling
- Segurança operacional

---

## 9. Saída do Agente

O retorno final do agente inclui:

- `resposta`: texto final gerado pelo modelo
- `agente`: identificador do agente (checkup)
- `tools_chamadas`: histórico de tools executadas
- `usage`: métricas de uso do modelo (tokens, etc.)

---

## 10. Considerações de Segurança

Por se tratar de um sistema voltado à saúde, o agente segue princípios críticos:

- Não substitui avaliação médica
- Não realiza diagnósticos definitivos
- Garante encaminhamento em situações de risco
- Limita o escopo de resposta para triagem

---

## 11. Conclusão

O Agente de Check-up Cardiovascular representa uma aplicação prática de IA conversacional aplicada à saúde, integrando:

- Modelos de linguagem (LLM)
- Function calling estruturado
- Recuperação de contexto (RAG)
- Fluxo determinístico de triagem médica

Sua arquitetura modular permite expansão futura para novos sensores, novas tools e integração com sistemas hospitalares, mantendo segurança e rastreabilidade como pilares centrais.
