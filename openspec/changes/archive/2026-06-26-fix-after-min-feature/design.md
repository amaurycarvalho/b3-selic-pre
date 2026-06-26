## Context

O feature `AFTER_MIN_UP` em `_features.py:123-133` computa a proporcao de deltas positivos apos o minimo global como `after_min_ratio = pos_deltas / total_deltas` sobre `rates[min_idx:]`. Isso inclui TODO o trecho apos o minimo — inclusive o platao longo e estavel tipico de curvas DI no longo prazo. Deltas zero (taxa nao mudou) sao tratados como nao-positivos, destruindo a proporcao.

Exemplo real: curva com minimo em 14.03 (indice 39), recuperacao ate 14.37 (indice ~170), e platao em 14.23 ate o final. Apos o minimo: 36 deltas positivos, 18 negativos, **186 zeros**. `after_min_ratio = 36/240 = 0.15`, muito abaixo de 0.80.

O mesmo problema afeta `AFTER_MAX_DOWN` (`_features.py:136-147`).

## Goals / Non-Goals

**Goals:**
- Restringir `AFTER_MIN_UP` a janela [min_idx, max_idx] — zona de recuperacao entre minimo e maximo globais
- Restringir `AFTER_MAX_DOWN` a janela [max_idx, min_idx] — zona de descida entre maximo e minimo globais
- Preservar o threshold `recuperacao_min_ratio` (0.80) — apenas a janela de analise muda

**Non-Goals:**
- Alterar thresholds existentes
- Alterar outras features
- Criar novas features ou regras
- Modificar o classificador ou scoring

## Decisions

### D1: Janela limitada ao intervalo entre extremos

**Problema:** `after_min = rates[min_idx:]` inclui o platao, onde deltas zero dominam.

**Decisao:** Substituir por `rates[min_idx:max_idx+1]` quando `max_idx > min_idx`. Usar o ULTIMO indice do valor minimo como inicio da janela (nao o primeiro), para excluir o chao do vale onde a taxa ainda nao comecou a subir.

```python
if max_idx > min_idx:
    min_val = rates[min_idx]
    last_min = max(i for i, r in enumerate(rates) if r == min_val)
    recovery_start = min(last_min, max_idx - 1)
    recovery_zone = rates[recovery_start:max_idx + 1]
    after_min_deltas = [...]
```

### D2: Deltas zero contam como "recuperando"

**Problema:** `d > 0` trata deltas zero (taxa estavel) como falha de recuperacao. Curvas DI tem muitos deltas zero devido a taxas repetidas em DU consecutivos (ex: `14.05, 14.05, 14.05` → 2 deltas zero).

**Decisao:** Usar `d >= 0` para AFTER_MIN_UP e `d <= 0` para AFTER_MAX_DOWN. Uma taxa que nao desceu durante a zona de recuperacao e consistente com recuperacao sustentada.

```python
pos_after_min = sum(1 for d in after_min_deltas if d >= 0)  # era: d > 0
neg_after_max = sum(1 for d in after_max_deltas if d <= 0)   # era: d < 0
```

**Problema:** Se o maximo global ocorre antes ou na mesma posicao que o minimo, nao ha zona de recuperacao definida.

**Decisao:** Retornar `after_min_deltas = []`, resultando em `after_min_ratio = 0.0` e `AFTER_MIN_UP = False`. Isso e consistente: se nao ha maximo depois do minimo, nao houve recuperacao.

## Risks / Trade-offs

- **[Risco] Curvas onde o maximo ocorre muito depois do fim da recuperacao real** (ex: maximo e um spike isolado no final) podem ter a janela estendida alem do necessario. → **Mitigacao:** O threshold de 80% ainda filtra ruido. Se o spike for real, ele faz parte da recuperacao. Se for espurio, a proporcao de deltas positivos ainda sera alta (o spike em si e um delta positivo).
- **[Risco] Curvas sem maximo claro depois do minimo** (ex: curva monotonicamente descendente) perdem AFTER_MIN_UP. → **Mitigacao:** Essas curvas nao sao VALE — o comportamento de retornar False e correto.
- **[Trade-off] Mudanca de comportamento para curvas existentes** → **Beneficio:** Curvas com vale+recuperacao+plato passam a ser corretamente detectadas.
