## Why

O feature `AFTER_MIN_UP` computa a proporcao de deltas positivos apos o minimo global usando `after_min = rates[min_idx:]` — toda a cauda da curva. Em curvas DI tipicas, o trecho longo e essencialmente plano (deltas zero). Esses zeros sao tratados como nao-positivos e destroem a proporcao, fazendo `AFTER_MIN_UP` falhar mesmo quando a recuperacao entre o minimo e o maximo e clara e sustentada. Exemplo real: curva com 36 deltas positivos na subida, 18 negativos na descida e **186 zeros** no platao final — `after_min_ratio = 36/240 = 0.15`, muito abaixo do threshold 0.80. O mesmo problema afeta `AFTER_MAX_DOWN` para curvas com pico.

## What Changes

- **Restringir janela do `AFTER_MIN_UP` ao intervalo [min_idx, max_idx]**: em vez de analisar toda a cauda apos o minimo, limitar a analise a zona de recuperacao — do minimo global ate o maximo global (se o maximo ocorrer depois do minimo). **BREAKING**: altera o comportamento do feature `AFTER_MIN_UP`, podendo fazer curvas que antes falhavam passarem a ativar (e vice-versa).
- **Restringir janela do `AFTER_MAX_DOWN` ao intervalo [max_idx, min_idx]**: analogo para curvas com pico — analisar apenas a zona de descida do maximo ao minimo global. **BREAKING**: idem.
- **Adicionar fallback para quando max_idx <= min_idx**: se o maximo nao ocorre depois do minimo (ou vice-versa), o feature retorna False (nao ha zona de recuperacao/descida a analisar).

## Capabilities

### Modified Capabilities

- `auto-analysis`: Requisito de computacao das features `AFTER_MIN_UP` e `AFTER_MAX_DOWN` e alterado para restringir a janela de analise ao intervalo entre minimo e maximo globais.

## Impact

- **Arquivos modificados**:
  - `src/b3_selic_pre/application/analyze/_features.py` — logica de `AFTER_MIN_UP` e `AFTER_MAX_DOWN` (linhas ~123-147)
  - `tests/test_analyze.py` — atualizar testes existentes de VALE/PICO que dependem de AFTER_MIN_UP/AFTER_MAX_DOWN
