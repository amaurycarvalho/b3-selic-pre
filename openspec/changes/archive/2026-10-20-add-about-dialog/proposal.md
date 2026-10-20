## Why

A aplicação expõe versão apenas no título da janela e no `--version`, sem um local que reúna identidade, licença, apresentação e caminhos úteis para o usuário. Também não há como descobrir, pela interface, se existe uma versão mais nova publicada.

## What Changes

- Adicionar um botão "Sobre" na barra superior, com o ícone `help-about.png`, à direita do botão de copiar dados e visualmente separado dos botões de busca e cópia. O botão terá tooltip.
- Abrir uma janela modal com ícone da aplicação, nome e versão (`Taxas Referenciais SELIC (B3) vX.Y.Z`), data de lançamento ISO, licença GNU GPLv3 e texto curto de apresentação.
- Incluir no diálogo botões para abrir o repositório no navegador padrão, o diretório de logs no gerenciador de arquivos padrão e um botão "Fechar" que encerra o diálogo.
- Quando o diretório de logs não existir, informar a indisponibilidade dentro do próprio diálogo, sem criar o diretório e sem falhar silenciosamente.
- Introduzir `__release_date__` no pacote e atualizar a skill `release-version` para alterá-lo junto com a versão.
- Verificar a versão mais recente na API de releases do GitHub em background, na primeira abertura do diálogo, com cache por sessão. Quando houver versão mais nova, exibir o aviso "Nova versão vX.Y.Z disponível" e um botão para abrir a página da release. Falha, timeout ou resposta inválida não exibem aviso.
- Cobrir a lógica nova com testes headless, preservando o orçamento atual de testes de UI.

## Capabilities

### New Capabilities

- `about-dialog`: botão de acesso, janela modal de informações institucionais, links externos, abertura do diretório de logs, metadados de versão/lançamento e aviso de nova versão.

### Modified Capabilities

<!-- Nenhuma capacidade existente tem requisito alterado; o tooltip do novo botão é parte da nova capacidade. -->

## Impact

- `src/b3_selic_pre/__init__.py`: novo `__release_date__`.
- `src/b3_selic_pre/application/about.py`: informações do diálogo, comparação de versões e texto do aviso.
- `src/b3_selic_pre/infrastructure/links.py`: abertura de URLs e diretórios no sistema operacional.
- `src/b3_selic_pre/infrastructure/release_check.py`: consulta à API de releases do GitHub.
- `src/b3_selic_pre/presentation/gui/about.py`: janela modal.
- `src/b3_selic_pre/presentation/gui/app.py`: botão, ícone e espaçamento da barra superior.
- `src/b3_selic_pre/presentation/gui/dependencies.py` e `launch.py`: novos adapters injetáveis.
- `.opencode/skills/release-version/SKILL.md`: atualização da data de lançamento.
- `tests/`: novos testes headless; nenhum aumento no orçamento de testes de UI.
- A consulta ao GitHub é opcional e best-effort. Ela não substitui a API da B3 nem vira dependência funcional da aplicação.
