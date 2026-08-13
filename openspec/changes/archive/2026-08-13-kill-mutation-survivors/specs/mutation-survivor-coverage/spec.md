## ADDED Requirements

### Requirement: Survivors matáveis são mortos por testes dedicados

Cada mutante sobrevivente (`exit_code == 0` em `mutants/src/**/*.meta`) classificado como matável SHALL ser morto por um teste dedicado adicionado ou modificado na suíte, sem executar `mutmut`.

#### Scenario: teste dedicado mata um survivor matável
- **WHEN** um survivor matável é identificado (mutação detectável por algum input/assertiva)
- **THEN** um teste novo ou modificado na suíte passa a matar esse survivor quando executado via `pytest` (a mutação torna o teste vermelho)
- **THEN** o teste é validado executando somente ele (`pytest tests/<arquivo>::<classe>::<teste>`), nunca via `mutmut run`

#### Scenario: survivor já coberto não gera teste redundante
- **WHEN** um survivor é verificado e o comportamento mutado já é coberto por uma assertiva existente
- **THEN** nenhum teste adicional é escrito para esse survivor

### Requirement: Mutantes equivalentes são pulados e documentados

Mutantes equivalentes (impossíveis de matar por qualquer input — comportamento idêntico ao original para todos os inputs) SHALL ser pulados e documentados numa lista explícita, em vez de receber testes.

#### Scenario: equivalente documentado e ignorado
- **WHEN** um survivor é classificado como equivalente (nenhum input distingue a mutação)
- **THEN** o survivor é registrado numa lista de exceção com o motivo da equivalência
- **THEN** nenhum teste é criado para ele

### Requirement: Survivors agrupados por módulo

A análise dos survivors SHALL ser organizada por módulo (e, dentro do módulo, por função), seguindo a ordem de prioridade de custo × impacto definida no design.

#### Scenario: análise por módulo
- **WHEN** a análise dos survivors é realizada
- **THEN** os survivors são enumerados e classificados por módulo de origem (`application.*`, `infrastructure.*`, `presentation.*`)

### Requirement: Invariantes de qualidade preservados

Após adicionar os testes, `make lint` SHALL permanecer limpo e `make test` SHALL passar com cobertura >= 85%.

#### Scenario: lint limpo
- **WHEN** os novos testes são adicionados
- **THEN** `make lint` (ruff + flake8) não acusa novas violações

#### Scenario: suíte completa verde
- **WHEN** `make test` executa a suíte completa
- **THEN** todos os testes passam e a cobertura permanece >= 85%
