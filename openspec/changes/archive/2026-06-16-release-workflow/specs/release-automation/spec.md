## ADDED Requirements

### Requirement: Build executáveis multiplataforma
O sistema SHALL gerar executáveis do `b3-selic-pre` para Windows, Linux e macOS via PyInstaller em um workflow GitHub Actions.

#### Scenario: Build em todos os OS
- **WHEN** o workflow é disparado
- **THEN** o job `build` executa nos runners `ubuntu-latest`, `windows-latest` e `macos-latest`
- **THEN** cada runner gera um executável com PyInstaller no formato `--onefile`

#### Scenario: Falha em um OS não bloqueia os demais
- **WHEN** o build falha em um runner específico
- **THEN** os demais runners continuam e produzem seus artefatos
- **THEN** o job `release` NÃO é executado (release depende de sucesso total)

### Requirement: Publicar GitHub Release
O workflow SHALL criar uma GitHub Release contendo todos os executáveis gerados como assets.

#### Scenario: Release automática por tag
- **WHEN** um push de tag no formato `v*` (ex: `v1.0.0`) é feito
- **THEN** o workflow é disparado
- **THEN** ao final, uma GitHub Release é criada com os binários

#### Scenario: Release manual
- **WHEN** o workflow é disparado manualmente via `workflow_dispatch`
- **THEN** o comportamento é idêntico ao disparo por tag

### Requirement: Nomear binários por plataforma
Os artefatos gerados SHALL seguir a convenção de nomenclatura:

- Linux: `b3-selic-pre-linux`
- Windows: `b3-selic-pre-windows.exe`
- macOS: `b3-selic-pre-macos`

#### Scenario: Artefatos nomeados por plataforma
- **WHEN** o build conclui em cada runner
- **THEN** o artefato gerado tem o nome correspondente à plataforma

### Requirement: Incluir dependências de sistema no Linux
O runner Linux SHALL instalar `python3-tk` via apt antes do build para disponibilizar o tkinter.

#### Scenario: tkinter disponível no build Linux
- **WHEN** o workflow executa no runner Linux
- **THEN** o comando `sudo apt-get install -y python3-tk` é executado antes do PyInstaller
- **THEN** o PyInstaller consegue empacotar o tkinter

### Requirement: Incluir arquivo .desktop no release Linux
O release do Linux SHALL incluir o arquivo `b3-selic-pre.desktop` como asset adicional.

#### Scenario: Desktop file incluso
- **WHEN** o job `release` é executado
- **THEN** o asset `b3-selic-pre-linux.desktop` (ou o `.desktop` original) é incluído entre os arquivos do release para Linux

### Requirement: .spec versionado
O projeto SHALL manter um arquivo `b3-selic-pre.spec` versionado na raiz, contendo toda a configuração do PyInstaller (hidden imports, add-data, flags, etc.).

#### Scenario: Spec usado como fonte única de build
- **WHEN** o workflow executa o PyInstaller
- **THEN** ele utiliza `b3-selic-pre.spec` como entrada, não flags avulsas na linha de comando

### Requirement: CHANGELOG.md
O projeto SHALL manter um arquivo `CHANGELOG.md` na raiz documentando as versões publicadas, seguindo o formato baseado em [Keep a Changelog](https://keepachangelog.com/).

#### Scenario: CHANGELOG versionado
- **WHEN** uma nova release é criada
- **THEN** o `CHANGELOG.md` contém uma entrada para a versão correspondente antes do tag ser criado

### Requirement: Disparo do workflow
O workflow SHALL ser disparado por push de tag `v*` OU por `workflow_dispatch` manual.

#### Scenario: Disparo por tag
- **WHEN** um push contém uma tag começando com `v`
- **THEN** o workflow é iniciado

#### Scenario: Disparo manual
- **WHEN** um usuário acessa a aba Actions do repositório e seleciona "Run workflow"
- **THEN** o workflow é iniciado
