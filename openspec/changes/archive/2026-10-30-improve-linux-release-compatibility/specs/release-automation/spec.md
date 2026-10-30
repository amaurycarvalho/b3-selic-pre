# Spec Delta

## MODIFIED Requirements

### Requirement: Build executáveis multiplataforma
O sistema SHALL gerar executáveis do `b3-selic-pre` para Windows, Linux e macOS via PyInstaller em um workflow GitHub Actions, após aprovação do quality gate.

#### Scenario: Build em todos os OS
- **WHEN** o workflow é disparado E o job `ci` conclui com sucesso
- **THEN** o job `build-linux` executa no runner `ubuntu-24.04` e o job `build-desktop` executa nos runners `windows-2025` e `macos-26`
- **THEN** cada job executa `make install && make build`
- **THEN** o PyInstaller gera o executável no diretório `dist/`
- **THEN** o binário é renomeado com prefixo da plataforma (`b3-selic-pre-linux`, `b3-selic-pre-windows.exe`, `b3-selic-pre-macos`)

#### Scenario: Build Linux em ambiente fixo
- **WHEN** o job `build-linux` é executado
- **THEN** o build ocorre dentro de um container baseado em Ubuntu 24.04, independente da imagem do runner
- **THEN** o binário resultante não exige versão de glibc superior à do Ubuntu 24.04

#### Scenario: Falha em um OS não bloqueia os demais
- **WHEN** o build falha em um runner específico
- **THEN** os demais runners continuam e produzem seus artefatos
- **THEN** o job `release` NÃO é executado (release depende de sucesso total)

### Requirement: Incluir dependências de sistema no Linux
O job Linux SHALL instalar Python 3.12 e Tk dentro do container de build, garantindo que o `tkinter` seja empacotado no executável.

#### Scenario: tkinter disponível no build Linux
- **WHEN** o job `build-linux` executa no container Ubuntu 24.04
- **THEN** `python3.12`, `python3.12-venv` e `python3.12-tk` são instalados a partir dos repositórios oficiais antes do PyInstaller
- **THEN** o build usa o Python 3.12 instalado
- **THEN** o PyInstaller consegue empacotar o tkinter

## ADDED Requirements

### Requirement: Compatibilidade do binário Linux com Ubuntu 24.04
O executável Linux publicado SHALL ser construído em ambiente com glibc 2.39 ou inferior, para executar em Ubuntu 24.04 e distribuições mais recentes.

#### Scenario: Execução em Ubuntu 24.04
- **WHEN** o usuário executa o binário `b3-selic-pre-linux` em Ubuntu 24.04
- **THEN** o binário inicia sem erro de versão de `GLIBC`
- **THEN** o `tkinter` carrega e a interface gráfica abre
