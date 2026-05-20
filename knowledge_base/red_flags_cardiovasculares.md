# Red Flags Cardiovasculares — Sinais de Alerta
## BluaDiagnostics — Base de Conhecimento Clínico
### Fonte: Diretrizes SBC 2025, Protocolo Manchester, literatura cardiovascular
### Versão: 1.0.0 | 2026-05-15

---

## 1. O que são Red Flags Cardiovasculares

Red flags — sinais de alerta — são sintomas ou combinações de
sintomas que indicam alta probabilidade de condição cardiovascular
grave com risco de morte ou sequela permanente. A identificação
imediata de uma red flag é a função mais crítica do agente
BluaDiagnostics.

Princípio fundamental: na presença de qualquer red flag, o agente
prioriza a escalada para atendimento de emergência acima de qualquer
outra ação. Não coleta informações adicionais. Não agenda teleconsulta.
Instrui SAMU 192 imediatamente.

---

## 2. Red Flags de Infarto Agudo do Miocárdio (IAM)

O infarto ocorre quando uma artéria coronária é obstruída e parte
do músculo cardíaco começa a morrer por falta de oxigênio. Cada
minuto conta — o dano é proporcional ao tempo sem reperfusão.

### Sintomas clássicos
- Dor ou pressão intensa no centro do peito, como um "aperto" ou
  "peso", com duração superior a 15 minutos
- Irradiação da dor para braço esquerdo, ombro esquerdo, mandíbula,
  pescoço ou costas
- Dor que não melhora com repouso nem com mudança de posição
- Suor frio intenso associado à dor torácica
- Falta de ar súbita junto com dor no peito
- Náusea ou vômito associados à dor torácica

### Sintomas atípicos — igual atenção
- Em mulheres: fadiga extrema inexplicável, náusea isolada, dor
  nas costas ou mandíbula sem dor torácica
- Em idosos: dispneia súbita como único sintoma
- Em diabéticos: mal-estar vago, sudorese, sem dor típica

### Conduta imediata
Instrução ao beneficiário: "Ligue agora para 192 (SAMU). Não
dirija. Mastigue um comprimido de AAS 100mg ou 500mg se disponível
e não houver alergia conhecida. Aguarde o socorro deitado ou
sentado na posição mais confortável."

---

## 3. Red Flags de Acidente Vascular Cerebral (AVC)

O AVC ocorre quando o fluxo sanguíneo para parte do cérebro é
interrompido — por obstrução (isquêmico, 85% dos casos) ou
ruptura de vaso (hemorrágico). O AVC isquêmico tem janela
terapêutica de até 4,5 horas para trombólise — cada minuto sem
tratamento representa perda de 1,9 milhão de neurônios.

### Método FAST para identificação rápida
- **F** — Face: assimetria facial, boca torta ao sorrir
- **A** — Arms: fraqueza ou dormência em um braço
- **S** — Speech: dificuldade de fala, palavras embaralhadas,
  incapacidade de repetir uma frase simples
- **T** — Time: tempo é fundamental — ligar 192 imediatamente

### Outros sintomas de AVC
- Confusão mental súbita
- Perda de visão em um olho ou em um campo visual
- Cefaleia súbita e intensa "como nunca sentida antes"
- Perda de equilíbrio ou coordenação súbita

### Conduta imediata
Instrução ao beneficiário: "Isso pode ser um AVC. Ligue agora para
192 (SAMU). Não dê nada para comer ou beber. Anote o horário em
que os sintomas começaram."

---

## 4. Red Flags de Crise Hipertensiva

Crise hipertensiva é definida como pressão arterial acima de
180x120 mmHg. Divide-se em duas categorias:

### Urgência Hipertensiva
PA acima de 180x120 mmHg sem lesão aguda de órgão-alvo.
Sintomas: cefaleia intensa, tontura, zumbido, mal-estar geral.
Conduta: teleconsulta urgente — redução gradual da pressão em
24 a 48 horas.

### Emergência Hipertensiva
PA acima de 180x120 mmHg COM lesão aguda de órgão-alvo.
Sintomas associados: dor torácica, dispneia, déficit neurológico,
alteração de consciência, sangramento.
Conduta: SAMU 192 — redução controlada em ambiente hospitalar.

### Atenção crítica
Não orientar o beneficiário a tomar dose extra de anti-hipertensivo
por conta própria — redução abrupta da pressão pode ser tão
perigosa quanto a crise em si, especialmente em idosos e pacientes
com doença arterial coronariana.

---

## 5. Red Flags de Arritmia Grave

Arritmias podem ser benignas e fisiológicas — como a arritmia
sinusal — ou potencialmente fatais. Os sinais que indicam arritmia
grave são:

### Sinais de alto risco
- Síncope (desmaio) associada a palpitações
- Pré-síncope (quase desmaio, escurecimento visual) com
  batimentos irregulares
- Palpitações intensas e sustentadas com hipotensão
- FC acima de 150 bpm em repouso com mal-estar
- FC abaixo de 40 bpm com tontura ou dispneia

### Fibrilação atrial com resposta ventricular alta
Pacientes com FA conhecida que desenvolvem FC acima de 120 bpm
em repouso com sintomas (dispneia, tontura, dor torácica) devem
ser avaliados com urgência — risco de descompensação
hemodinâmica.

### Integração com ML
O modelo de detecção de arritmias classifica o ritmo como regular
ou irregular. Classificação irregular com qualquer sintoma associado
acima eleva automaticamente o nível de triagem para laranja ou
vermelho.

---

## 6. Red Flags de Insuficiência Cardíaca Descompensada

Pacientes com IC conhecida — como BENEF-002 no sistema — devem
ser monitorados para sinais de descompensação:

- Ganho de peso súbito acima de 2kg em 24 a 48 horas
- Piora progressiva da dispneia — falta de ar que antes ocorria
  só ao esforço agora ocorre em repouso
- Ortopneia — necessidade de dormir com mais travesseiros para
  não sentir falta de ar
- Dispneia paroxística noturna — acorda de madrugada com falta
  de ar intensa
- Edema de membros inferiores progressivo
- Tosse seca persistente, especialmente à noite

Conduta: teleconsulta urgente ou pronto-socorro conforme gravidade.

---

## 7. O que NÃO é Red Flag Cardiovascular

Para evitar superestimação de urgência e desgaste do beneficiário,
o agente deve saber distinguir sintomas que não configuram red flag
isoladamente:

- Palpitações rápidas episódicas após café, exercício ou emoção,
  sem mal-estar associado — geralmente extrassístoles fisiológicas
- Pressão arterial entre 140x90 e 160x100 em paciente hipertenso
  conhecido, sem sintomas agudos
- Tontura postural ao levantar rapidamente — hipotensão ortostática,
  frequentemente benigna
- Dor torácica que melhora completamente com mudança de posição
  ou inspiração profunda — sugestivo de origem musculoesquelética
  ou pleurítica, não cardíaca

Esses casos devem ser avaliados mas não constituem emergência.

---

*Documento elaborado para fins acadêmicos. Não substitui protocolo
clínico institucional nem avaliação médica presencial.*
*Em emergência: ligue 192 (SAMU).*