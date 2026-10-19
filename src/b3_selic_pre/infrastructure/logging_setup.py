"""Configuração central de logging com arquivo diário e retenção."""

from __future__ import annotations

import logging
import logging.handlers
import os
import shutil
import time
from datetime import date, timedelta
from pathlib import Path

from b3_selic_pre.infrastructure.xdg import cache_base

LOG_ACTIVE_NAME = "b3-selic-pre.log"
LOG_BACKUP_PREFIX = "b3-selic-pre-"
LOG_BACKUP_GLOB = "b3-selic-pre-????-??-??.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def log_dir() -> Path:
    """Return the application log directory under the platform cache base."""
    return cache_base() / "b3-selic-pre" / "logs"


def _local_today() -> date:
    """Return the current date in the local timezone."""
    now = time.localtime()
    return date(now.tm_year, now.tm_mon, now.tm_mday)


def _backup_path(active_path: Path, day: date) -> Path:
    return active_path.with_name(f"{LOG_BACKUP_PREFIX}{day.isoformat()}.log")


def _ends_with_newline(path: Path) -> bool:
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            return True
        stream.seek(-1, os.SEEK_END)
        return stream.read(1) == b"\n"


def _append_file(target: Path, source: Path) -> None:
    needs_separator = (
        target.exists()
        and target.stat().st_size > 0
        and not _ends_with_newline(target)
    )
    with target.open("ab") as destination, source.open("rb") as origin:
        if needs_separator:
            destination.write(b"\n")
        shutil.copyfileobj(origin, destination)


def rotate_stale_log(active_path: Path, today: date | None = None) -> Path | None:
    """Rename an active log from a previous local day to its dated backup."""
    current_day = today or _local_today()
    if not active_path.exists():
        return None
    modified = time.localtime(active_path.stat().st_mtime)
    modification_day = date(modified.tm_year, modified.tm_mon, modified.tm_mday)
    if modification_day >= current_day:
        return None
    target = _backup_path(active_path, modification_day)
    if target.exists():
        _append_file(target, active_path)
        active_path.unlink(missing_ok=True)
    else:
        active_path.rename(target)
    return target


def purge_old_logs(
    directory: Path,
    retention_days: int,
    today: date | None = None,
) -> list[Path]:
    """Delete dated backups older than the retention window."""
    current_day = today or _local_today()
    try:
        cutoff = current_day - timedelta(days=retention_days)
    except OverflowError:
        cutoff = date.min
    removed = []
    if not directory.exists():
        return removed
    for path in sorted(directory.glob(LOG_BACKUP_GLOB)):
        if not path.is_file():
            continue
        stem = path.name[len(LOG_BACKUP_PREFIX) : -len(".log")]
        try:
            file_day = date.fromisoformat(stem)
        except ValueError:
            continue
        if file_day < cutoff:
            try:
                path.unlink()
            except OSError:
                continue
            removed.append(path)
    return removed


def _daily_namer(default_name: str) -> str:
    path = Path(default_name)
    date_suffix = path.suffix.lstrip(".")
    active_stem = path.stem.removesuffix(".log")
    return str(path.with_name(f"{active_stem}-{date_suffix}.log"))


def _make_handler(active_path: Path) -> logging.Handler:
    handler = logging.handlers.TimedRotatingFileHandler(
        active_path,
        when="midnight",
        interval=1,
        backupCount=0,
        encoding="utf-8",
        delay=False,
        utc=False,
    )
    handler.namer = _daily_namer
    return handler


def configure_logging(
    log_directory: str | Path | None = None,
    retention_days: int | None = None,
    today: date | None = None,
) -> Path | None:
    """Configure the root logger and return the active log path."""
    try:
        directory = Path(log_directory) if log_directory else log_dir()
        directory.mkdir(parents=True, exist_ok=True)
        active_path = directory / LOG_ACTIVE_NAME
        rotate_stale_log(active_path, today=today)
        if retention_days is not None:
            purge_old_logs(directory, retention_days, today=today)
        handler = _make_handler(active_path)
        logging.basicConfig(
            level=logging.INFO,
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT,
            handlers=[handler],
            force=True,
        )
    except OSError:
        return None
    return active_path
