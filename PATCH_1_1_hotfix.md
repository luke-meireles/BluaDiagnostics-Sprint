# Patch 1.1 — Hotfix de superfície de API (`QwenClient` + `_modelo_padrao`)

> **Por que existe**: durante a validação do Patch 1, o Claude Code
> detectou (corretamente) duas incompatibilidades:
>
> - **Validação #2 falhou** porque o `qwen_client.py` do Sprint-main usa
>   `_MODELO_PADRAO` (constante de módulo, lida no import) em vez de
>   uma função `_modelo_padrao(backend)`.
> - **Validação #6 falhou** com `ImportError` porque o
>   `ollama_client.py` da Parte 2 importa `class QwenClient`, que não
>   existe no Sprint-main.
>
> A causa raiz é minha: o Patch 1 misturou conteúdo do `bluadiagnostics`
> (que tem API funcional **e** classe wrapper) sem tornar explícito que
> ambas as superfícies precisam existir.
>
> Este patch é **pequeno** (≈20 linhas alteradas), **conservador**
> (mantém a API funcional intacta) e **suficiente** para destravar as
> validações 2 e 6.

---

## Diagnóstico em 3 frases

1. `bluadiagnostics/src/llm/qwen_client.py` define função `_modelo_padrao(backend)` (resolução tardia) **E** classe `QwenClient` (wrapper OO sobre `chat()`).
2. O patch original copiou só **parte** disso para o Sprint-main — manteve a constante `_MODELO_PADRAO` antiga e nunca adicionou a classe.
3. O `ollama_client.py` da Parte 2 depende da classe; o teste de validação #2 depende da função. Ambos quebram.

---

## Mudanças

### Item 1 — Trocar `_MODELO_PADRAO` (constante) por `_modelo_padrao(backend)` (função)

**Arquivo**: `src/llm/qwen_client.py`

**Por quê**: a constante é resolvida no momento do `import`. Em Colab,
`colab_setup.preparar_ambiente()` roda **depois** do primeiro import,
então a variável de ambiente atualizada nunca é vista. A função
resolve no momento da chamada — comportamento correto.

**Localizar** (no topo do arquivo, perto dos outros consts):

```python
_MODELO_PADRAO = os.getenv("QWEN_DASHSCOPE_MODEL", "qwen-plus")
```

**Substituir por**:

```python
def _modelo_padrao(backend: str) -> str:
    """Lê o modelo no momento da chamada (não no import).

    Necessário porque `colab_setup.preparar_ambiente()` pode rodar
    depois do primeiro `import` deste módulo — se lêssemos no import,
    a variável atualizada seria ignorada.
    """
    if backend == "dashscope":
        return os.getenv("QWEN_DASHSCOPE_MODEL", "qwen-plus")
    return os.getenv("QWEN_OLLAMA_MODEL", "qwen:9b")
```

**Atualizar o ponto de uso dentro de `chat()`**:

```diff
- chosen_model = model or _MODELO_PADRAO
+ chosen_model = model or _modelo_padrao(backend)
```

> Se houver outros pontos que referenciam `_MODELO_PADRAO` (busque com
> `grep -n _MODELO_PADRAO src/`), substitua todos por
> `_modelo_padrao(backend)` passando o backend correspondente.

---

### Item 2 — Adicionar classe `QwenClient` no final de `qwen_client.py`

**Arquivo**: `src/llm/qwen_client.py`

**Por quê**: o `ollama_client.py` da Parte 2 depende dela. É um
wrapper de 5 linhas — não é refatoração arquitetural, é só açúcar OO
sobre a função `chat()` que já existe.

**Adicionar ao final do arquivo** (depois da função `chat()`):

```python
class QwenClient:
    """Versão OO da função `chat`, útil para fixar o backend uma vez.

    Equivalente funcional a chamar `chat(..., backend=self.backend)` em
    todo lugar — existe só para deixar explícito (e auditável via grep)
    qual backend cada consumidor usa.
    """

    def __init__(self, backend: Literal["dashscope", "ollama"] = "dashscope") -> None:
        self.backend = backend

    def chat(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("backend", self.backend)
        return chat(**kwargs)
```

**Importante**: a anotação `Literal["dashscope", "ollama"]` exige que
`Literal` esteja importado do `typing`. Confirma o topo do arquivo:

```python
from typing import Any, Literal
```

Se já está, ok. Se não, adicione.

---

### Item 3 — Atualizar `src/llm/__init__.py` para re-exportar `QwenClient`

**Arquivo**: `src/llm/__init__.py`

**Por quê**: o `ollama_client.py` importa de
`src.llm.qwen_client`, não de `src.llm`, então tecnicamente não
precisa do re-export. Mas o `__init__.py` é a fachada do pacote — é
boa prática deixar a classe visível ali também.

**Diff**:

```diff
- from src.llm.qwen_client import chat
+ from src.llm.qwen_client import QwenClient, chat
+ from src.llm.ollama_client import OllamaClient
  
- __all__ = ["chat"]
+ __all__ = ["QwenClient", "OllamaClient", "chat"]
```

---

## Validação pós-hotfix

Reproduzir as validações que falharam no Patch 1, mais uma terceira que
fecha o ciclo:

```bash
# Validação 2 (era falhou): _modelo_padrao agora é função
python -c "
import os
os.environ['QWEN_DASHSCOPE_MODEL'] = 'qwen-test'
from src.llm.qwen_client import _modelo_padrao
result = _modelo_padrao('dashscope')
assert result == 'qwen-test', f'esperado qwen-test, veio {result}'
print('ok validação 2:', result)
"

# Validação 6 (era ImportError): QwenClient existe e OllamaClient herda dela
python -c "
from src.llm.qwen_client import QwenClient
from src.llm.ollama_client import OllamaClient
oc = OllamaClient()
assert oc.backend == 'ollama', f'backend errado: {oc.backend}'
assert isinstance(oc, QwenClient), 'OllamaClient deveria herdar QwenClient'
print('ok validação 6: OllamaClient é QwenClient com backend', oc.backend)
"

# Validação extra: assinatura de chat() continua intacta (não regrediu)
python -c "
import inspect
from src.llm.qwen_client import chat
sig = inspect.signature(chat)
params = sig.parameters
assert 'messages' in params, 'messages sumiu'
assert params['messages'].annotation != inspect.Parameter.empty, 'anotação de messages sumiu'
assert params['temperature'].annotation is float, f'temperature deveria ser float, é {params[\"temperature\"].annotation}'
assert 'backend' in params, 'backend não existe em chat()'
print('ok assinatura preservada:', sig)
"
```

Se os 3 testes passam, as validações 2 e 6 do Patch 1 agora também
passam, e o `ollama_client.py` da Parte 2 fica utilizável de fato.

---

## Por que esta versão e não as alternativas

O Claude Code propôs duas alternativas:

1. **Refatorar `qwen_client.py` para envolver `chat()` numa classe** —
   mudança arquitetural maior, fora do escopo do hotfix.
2. **Reescrever `ollama_client.py` no estilo funcional do Sprint-main** —
   exigiria que `chat()` aceitasse `backend`, "mas `chat()` atual nem
   aceita `backend`".

A segunda observação está **parcialmente correta**: o `chat()` do
Sprint-main original não aceitava `backend`. **Mas** o Patch 1 já
introduziu o argumento `backend` na assinatura corrigida (a Parte 1
substitui a função inteira pela versão do `bluadiagnostics`).

Então o estado real depois do Patch 1 já é:
- ✅ `chat()` aceita `backend`.
- ❌ Falta `_modelo_padrao(backend)` (ainda usa `_MODELO_PADRAO` antigo).
- ❌ Falta `class QwenClient`.

Este hotfix corrige só os dois itens faltantes, sem desfazer nada.
Mantém o estilo funcional como API primária (`chat()` continua sendo
a "fachada principal" do módulo) e adiciona a classe como **camada
opcional** — exatamente o desenho do `bluadiagnostics` original, que
eu deveria ter copiado de forma íntegra desde o começo.

---

## Como aplicar com o Claude Code

Mesma sessão, mesmo workflow:

```
Detectamos que o Patch 1 ficou com superfície de API incompleta —
validações 2 e 6 falharam. Aplique agora o PATCH_1_1_hotfix.md, que
adiciona _modelo_padrao(backend) e class QwenClient ao qwen_client.py,
e atualiza o __init__.py do pacote llm. Depois, rode as 3 validações
da seção final do hotfix e me reporte.

Quando passar, re-rode também as validações 2 e 6 do Patch 1 original
pra confirmar que agora passam.
```

Depois de aplicado, o Patch 2 (cardiologia) pode seguir sem mexer
nesta parte — ele não toca em `qwen_client.py` nem em `ollama_client.py`.
