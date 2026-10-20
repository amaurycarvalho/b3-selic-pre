## Context

Ver `proposal.md` para motivação e `specs/application-logging/spec.md` para o contrato de comportamento.

O código atual não possui logging. O cliente HTTP usa `urllib.request` (`infrastructure/b3_client.py`), a GUI captura apenas `ConnectionError`, `TimeoutError` e `ValueError` no worker (`presentation/gui/fetch.py`) e a CLI não trata falhas. O cache já resolve caminhos XDG/plataforma em `infrastructure/disk_cache.py`. A arquitetura permite `infrastructure -> application`, mas proíbe `application -> urllib/requests` e só permite `presentation -> infrastructure` nos composition roots `presentation/cli.py` e `presentation/gui/launch.py`.

## Goals / Non-Goals

**Goals:**

- Centralizar configuração, formato, rotação e retenção de logs sem duplicar regras entre CLI e GUI.
- Manter o logging independente da biblioteca HTTP, para que a futura migração `urllib -> requests` não altere a camada de apresentação.
- Preservar o comportamento atual da GUI e da CLI em casos de sucesso, alterando apenas o tratamento de falhas.
- Manter todos os testes novos headless, respeitando o orçamento de testes de UI.

**Non-Goals:**

- Migrar o cliente HTTP para `requests`; isso será uma mudança separada.
- Criar UI para editar `log_retention_days`.
- Implementar lock ou escrita coordenada entre processos.
- Garantir rotação física exatamente às 00:00; a rotação é preguiçosa, conforme a spec.
- Alterar o formato ou o conteúdo da status bar da GUI.

## Decisions

### 1. Configuração central em `infrastructure/logging_setup.py`

O módulo expõe `configure_logging(...)`, chamado apenas pelos composition roots. Ele cria o diretório, executa a rotação de startup, opcionalmente a retenção, constrói o handler e chama:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[handler],
    force=True,
)
```

O handler é criado sem formatter (`formatter is None`), de modo que o `basicConfig` aplique o mesmo `format`/`datefmt` a ele. `force=True` evita handlers duplicados quando a configuração é reaplicada.

**Alternativa rejeitada:** configurar logging separadamente em CLI e GUI. Duplicaria formato, rotação e caminhos, além de permitir divergência entre os entry points.

### 2. Rotação diária com `TimedRotatingFileHandler`

Handler com `when="midnight"`, `interval=1`, `utc=False`, `backupCount=0`, `encoding="utf-8"` e `delay=False`. Um `namer` converte o nome padrão (`b3-selic-pre.log.YYYY-MM-DD`) em `b3-selic-pre-YYYY-MM-DD.log`. `backupCount=0` desliga a exclusão automática; a retenção é responsabilidade explícita da GUI.

A rotação é preguiçosa: o handler verifica a data antes de cada `emit`, então o primeiro registro após a meia-noite rotaciona antes de ser gravado. Se não houver registro, a rotação ocorre no próximo registro ou na próxima inicialização. Isso atende à spec e evita uma thread de timer.

**Alternativa rejeitada:** thread/timer que chama `doRollover` às 00:00. Adiciona ciclo de vida de thread, sincronização e testes de relógio sem benefício observável.

### 3. Ordem de inicialização: rotacionar, reter, abrir handler

Em `configure_logging`:

1. resolver e criar o diretório de logs;
2. rotacionar o arquivo ativo antigo, se necessário;
3. na GUI, apagar backups fora da retenção;
4. criar o handler e chamar `basicConfig`.

Rotacionar antes de reter garante que um arquivo ativo muito antigo, recém-rotacionado, seja considerado pela retenção na mesma inicialização.

A rotação de startup usa `datetime.fromtimestamp(path.stat().st_mtime).date()` (data local). Se o destino datado já existir, o conteúdo do ativo é anexado ao destino em modo binário, com separador de nova linha se necessário, e o ativo é removido. Isso evita a sobrescrita silenciosa do `Path.rename` no POSIX e a falha do `rename` no Windows.

### 4. Retenção somente na GUI

`purge_old_logs(log_dir, retention_days)` percorre apenas `b3-selic-pre-????-??-??.log`, valida a data com `date.fromisoformat` e remove arquivos com `file_date < today - timedelta(days=retention_days)`. Arquivos inválidos, o ativo e nomes fora do padrão são ignorados. `OSError` por arquivo é tolerado.

`retention_days` vem de `Settings.log_retention_days()`. Valores ausentes, não inteiros, booleanos ou menores que `1` viram `7`. Um inteiro grande que provoque `OverflowError` em `timedelta` é tratado como “manter tudo” (cutoff em `date.min`), sem quebrar a inicialização.

### 5. Base XDG compartilhada

Novo `infrastructure/xdg.py` com `cache_base()` contendo a lógica de plataforma hoje duplicada em `disk_cache.py`. `disk_cache` passa a usar `cache_base() / "b3-selic-pre" / "rates"`; `logging_setup` usa `cache_base() / "b3-selic-pre" / "logs"`.

**Alternativa rejeitada:** duplicar a lógica de plataforma no logging. Aumentaria a duplicação e permitiria caminhos divergentes entre cache e logs.

### 6. Contrato `CommunicationError` na application

`application/errors.py` define `CommunicationError(Exception)`. Em `infrastructure/cached_client.py`, um decorator envolve os métodos públicos de fetch e converte a família de rede/HTTP vigente em `CommunicationError`, preservando a causa:

```python
except NETWORK_EXCEPTIONS as exc:
    raise CommunicationError(str(exc) or type(exc).__name__) from exc
```

A tupla atual inclui `urllib.error.URLError` (cobre `HTTPError`), `http.client.HTTPException`, `TimeoutError`, `ConnectionError`, `ssl.SSLError` e `socket.gaierror`. Não se captura `OSError` amplo, para não classificar falhas de disco do cache como comunicação.

A migração futura para `requests` adiciona `requests.RequestException` à tupla; o logging e a presentation não mudam.

**Alternativas rejeitadas:** a presentation importar `urllib`/`requests` (acoplamento de camada e retrabalho na migração); detectar por nome de módulo (frágil e difícil de testar).

### 7. Classificação e logging em `presentation/logging_utils.py`

`is_communication_error(exc)` percorre `__cause__` e `__context__` com proteção contra ciclos e retorna `True` ao encontrar `CommunicationError` ou uma exceção da família de comunicação preservada na cadeia.

`log_exception(logger, exc, context)`:

- comunicação: localiza a exceção de rede/HTTP na cadeia, normaliza quebras de linha e grava uma única linha com contexto, tipo e mensagem, sem `exc_info`;
- não-comunicação: grava `logger.error(context, exc_info=(type(exc), exc, exc.__traceback__))`, preservando o traceback mesmo fora do bloco `except`.

O helper fica na presentation porque a application proíbe `urllib`/`requests`; ele depende apenas de `application.errors` e da stdlib.

### 8. Boundary de fetch da GUI

Os dois workers (`fetch_rates` e `_fetch_historical_rates`) passam a capturar `Exception`, chamar `log_exception` dentro do `except` e agendar a atualização da UI em `finally`. Isso preserva o `exc_info`, evita exceção não tratada na thread e garante que a status bar seja atualizada mesmo se o logging falhar.

**Alternativa rejeitada:** registrar em `handle_fetch_error`. Esse método roda via `root.after`, fora do contexto do `except`; sem `exc_info` explícito o traceback seria perdido.

### 9. Comportamento da CLI

A busca da CLI é envolvida em `try/except Exception`:

- comunicação: `log_exception` grava a linha única; a CLI imprime `Erro ao buscar dados: <mensagem>` em stderr e encerra com `SystemExit(1)`, sem traceback;
- não-comunicação: `log_exception` grava o traceback e a exceção é relançada.

O log é configurado para os caminhos de busca; `--help`, `--version` e `--create-shortcut` não criam arquivo de log.

### 10. Hooks de exceções não tratadas

`install_exception_hooks()` instala `sys.excepthook` e `threading.excepthook`. `install_tk_exception_hook(root)` instala `root.report_callback_exception`. Os hooks usam `log_exception` com o traceback capturado. O hook original só é chamado quando `sys.stderr` está disponível, evitando falhas em builds PyInstaller em modo janela (sem console).

### 11. Settings

`presentation/settings.py` adiciona `log_retention_days: 7` a `DEFAULT_SETTINGS` e o método `log_retention_days()`. Booleanos são rejeitados explicitamente, apesar de `bool` ser subclasse de `int`. A validação fica em `Settings` porque ele é o adapter do contrato do arquivo e já centraliza os defaults.

### 12. Registro de início e resiliência

Cada execução grava uma linha INFO com versão, modo (CLI/GUI) e caminho do arquivo ativo. A configuração de logging captura `OSError` ao criar diretório/handler e continua sem logging; uma falha de logging nunca impede a inicialização ou a operação.

Não há `StreamHandler`: a CLI imprime sua mensagem amigável separadamente e a GUI usa a status bar.

## Risks / Trade-offs

- **Rotação preguiçosa não renomeia às 00:00 exatas** → nenhum registro do novo dia é gravado no arquivo antigo; a próxima inicialização cobre o caso sem atividade. Aceito pela spec.
- **CLI e GUI simultâneas competem pela rotação do mesmo arquivo** → limitação documentada; não haverá lock nesta mudança. Recomenda-se não manter os dois modos ativos ao mesmo tempo.
- **Colisão de backup com linha parcial** → a anexação usa modo binário e insere separador de nova linha quando o destino não termina em newline.
- **Falha ao criar o log deixa a aplicação sem diagnóstico** → a aplicação continua funcionando; a falha não é fatal, conforme a spec.
- **`CommunicationError` muda o tipo de exceção no boundary do cliente** → a mensagem original é preservada e os testes de `cached_client`/GUI/CLI serão ajustados.
- **Migração futura para `requests` pode esquecer de atualizar a tupla de rede** → a mudança de migração deve incluir um teste explícito de `RequestException`; até lá, a tupla atual cobre o cliente `urllib`.
- **`basicConfig(force=True)` remove handlers preexistentes** → a aplicação não configura logging antes; a reaplicação fecha o handler anterior e evita duplicação.
- **Inteiro de retenção muito grande** → `OverflowError` é tratado como “manter tudo”, sem quebrar a inicialização.
- **Hooks globais podem duplicar a saída no stderr** → o log é a fonte de verdade; o hook original só é chamado quando há stderr.

## Migration Plan

- Não há migração de dados. Se existir um `b3-selic-pre.log` de execução anterior, a rotação de startup o move para o backup datado antes de abrir o novo handler.
- A mudança é aditiva; rollback consiste em remover as chamadas de configuração/hooks dos composition roots. Os arquivos de log existentes podem permanecer no disco.
- Nenhuma dependência nova e nenhuma alteração de banco ou formato persistido além da nova chave de settings.
- Validação: testes headless de logging/settings/CLI/cache, `make lint`, `make complexity` e suíte completa, por tocar infraestrutura compartilhada, CLI e GUI.
