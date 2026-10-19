## Why

A aplicação não possui logging: falhas de rede viram traceback no stderr (ou desaparecem no modo gráfico), não há histórico persistente por dia, nem retenção controlada. Isso dificulta diagnosticar falhas já toleradas pela interface e preservar o rastreio de defeitos inesperados.

## What Changes

- Criar um subsistema de logging compartilhado por CLI e GUI, com registros formatados com data/hora local e gravados em arquivo diário.
- Configurar o formato via `format`/`datefmt` do `logging.basicConfig`, aplicando o mesmo formato a todos os handlers da aplicação.
- Rotacionar o arquivo ativo `b3-selic-pre.log` na virada do dia local para `b3-selic-pre-YYYY-MM-DD.log`, de forma preguiçosa no primeiro registro após a meia-noite.
- Na inicialização, rotacionar o arquivo ativo cuja data de modificação seja anterior ao dia local corrente, usando a data da última modificação; se o backup de destino existir, anexar o conteúdo e remover o ativo.
- Na inicialização da GUI, apagar backups datados anteriores a `hoje - N`, preservando o dia corrente e os `N` dias anteriores; nunca apagar o arquivo ativo nem nomes fora do padrão datado.
- Ler `N` de `log_retention_days` em `settings.json`, com padrão `7` e fallback para ausente, não inteiro, booleano ou menor que `1`.
- Introduzir o contrato `CommunicationError` na camada `application`; a infraestrutura mapeia a família de rede/HTTP vigente (hoje `urllib`; futuramente `requests`, em mudança separada).
- Registrar falhas de comunicação toleradas em uma única linha, com tipo e mensagem da exceção, sem call stack; registrar qualquer outra exceção com traceback completo.
- Aplicar o mesmo tratamento no boundary de fetch da GUI e da CLI. Na CLI, falhas de comunicação geram mensagem amigável em stderr e saída com código `1`; falhas não-comunicação registram traceback e são relançadas.
- Instalar hooks de exceções não tratadas (`sys.excepthook`, `threading.excepthook` e `Tk.report_callback_exception`) para registrar defeitos inesperados com traceback.
- Reutilizar a base XDG/plataforma do cache para o diretório `.../b3-selic-pre/logs/`, em vez de duplicar a lógica de caminho.

## Capabilities

### New Capabilities

- `application-logging`: configuração de logging, formato com timestamp, rotação diária, retenção, classificação de falhas de comunicação e hooks de exceções não tratadas.

### Modified Capabilities

- `persistence`: adiciona a chave `log_retention_days` ao arquivo de settings, com padrão `7` e fallback para valores inválidos.

## Impact

- Novos módulos: `application/errors.py`, `infrastructure/logging_setup.py`, `presentation/logging_utils.py` e um helper compartilhado de caminhos XDG em `infrastructure/`.
- Alterações em `infrastructure/b3_client.py`, `infrastructure/cached_client.py`, `infrastructure/disk_cache.py`, `presentation/settings.py`, `presentation/cli.py`, `presentation/gui/launch.py` e `presentation/gui/fetch.py`.
- Novos testes headless para configuração, rotação, retenção, classificação de exceções, hooks e settings; atualização de testes de CLI e cache.
- Nenhuma dependência externa nova nesta mudança.
- A migração de `urllib` para `requests` fica fora de escopo e será tratada em outra mudança.
- Não há UI para editar `log_retention_days`; o valor é lido do arquivo de settings.
- Limitação conhecida: dois processos (CLI e GUI) escrevendo no mesmo arquivo diário podem competir na rotação; não haverá lock entre processos nesta mudança.
