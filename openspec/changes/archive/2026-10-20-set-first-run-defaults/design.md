## Context

Ver `proposal.md` para motivação. O estado atual relevante:

- `Settings` inicia `_data` com `DEFAULT_SETTINGS` e sobrescreve com o arquivo, quando existe; grava apenas em `set()`.
- `SelicPreApp._apply_saved_settings()` já lê `view_mode`, `evolution` e `sidebar`, então os novos padrões fluem para a GUI sem alteração no composition root.
- Sidebar ligada agenda `_toggle_sidebar` após 10 ms; evolução ligada faz a primeira busca carregar também o histórico.
- `tests/test_settings.py` fixa atualmente os defaults antigos (`raw`, evolução off, sidebar off).
- O orçamento de testes de UI está cheio; a mudança deve ser coberta por testes headless.

## Goals / Non-Goals

**Goals:**

- Distinguir a primeira execução (arquivo ausente) de um arquivo existente, válido ou corrompido.
- Aplicar os novos defaults somente na primeira execução.
- Manter os defaults de compatibilidade para arquivos existentes que omitam chaves.
- Cobrir a regra inteiramente em testes headless.

**Non-Goals:**

- Não alterar a data padrão, o 3D, a persistência do formato ou o comportamento de buscas.
- Não criar um mecanismo de migração de settings existentes.
- Não adicionar testes de UI novos.

## Decisions

### Detecção de primeira execução por ausência do arquivo

- Em `Settings.__init__`, verificar `self.path.exists()` antes de carregar e guardar o resultado em um atributo/propriedade de primeira execução.
- Apenas ausência de arquivo caracteriza primeira execução. Arquivo vazio (`{}`), inválido, JSON não-objeto ou arquivo válido sem uma chave NÃO são primeira execução.
- Alternativa considerada: considerar qualquer arquivo sem as chaves como primeira execução. Rejeitada porque alteraria usuários existentes com settings parciais/corrompidos.

### Defaults separados de compatibilidade

- Manter `DEFAULT_SETTINGS` com os valores de compatibilidade atuais (`view_mode="raw"`, `evolution=False`, `sidebar=False`, `show_3d=False`).
- Introduzir `FIRST_RUN_DEFAULTS` com `view_mode="consolidated"`, `evolution=True` e `sidebar=True`.
- Na primeira execução, montar `_data` a partir de `DEFAULT_SETTINGS` sobreposto por `FIRST_RUN_DEFAULTS`; em qualquer outro caso, manter o comportamento atual (`DEFAULT_SETTINGS` + arquivo válido).
- Alternativa considerada: mudar `DEFAULT_SETTINGS` diretamente. Rejeitada porque alteraria silenciosamente arquivos válidos que não contenham essas chaves.

### Persistência continua preguiçosa

- Não gravar o arquivo apenas por abrir a aplicação. O primeiro `Settings.set()` persiste `_data`, que já contém os defaults de primeira execução.
- Enquanto o arquivo não existir, cada abertura reaplica os mesmos defaults; o estado observado é idêntico e evita I/O e efeitos colaterais no construtor.
- Alternativa considerada: gravar o arquivo no primeiro `Settings()`. Rejeitada por criar configuração como efeito de simples inicialização e por complicar testes e ambientes sem permissão de escrita.

### GUI sem lógica adicional

- `SelicPreApp` continua aplicando os valores lidos de `Settings`; o sidebar expandido e o histórico na primeira busca são consequências naturais do estado inicial.
- A alteração do comportamento "sidebar começa recolhido" fica restrita à primeira execução; nos demais casos o requisito continua valendo.

## Risks / Trade-offs

- [Primeira busca com evolução ligada carrega histórico e demora mais] → comportamento intencional; a interface continua exibindo o estado de carregamento existente.
- [Arquivo existente mas corrompido não recebe os novos defaults] → mantém a compatibilidade e evita mudança inesperada; coberto por teste.
- [Usuário nunca altera preferências e o arquivo nunca é criado] → cada abertura usa exatamente os mesmos defaults de primeira execução; não há diferença observável.
- [Conflito com o requisito anterior de sidebar sempre recolhida] → resolvido pela delta da capability `auto-analysis`.

## Migration Plan

- Sem migração de dados. `settings.json` existente é carregado como antes.
- Rollback: remover `FIRST_RUN_DEFAULTS` e a detecção de primeira execução, restaurando `DEFAULT_SETTINGS` como único ponto de defaults.
