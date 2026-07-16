import base64
import concurrent.futures
import json
import math
import urllib.request

from b3_selic_pre.domain.constants import (
    B3_BASE_URL,
    DEFAULT_LANGUAGE,
    DEFAULT_MAX_PAGES,
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RATE_ID,
    EVOLUTION_DAYS,
)
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.application.use_cases import _days_ago, validate_reference_date


def build_payload(
    reference_date,
    language=DEFAULT_LANGUAGE,
    rate_id=DEFAULT_RATE_ID,
    page_number=DEFAULT_PAGE_NUMBER,
    page_size=DEFAULT_PAGE_SIZE,
):
    return {
        "language": language,
        "id": rate_id,
        "pageNumber": page_number,
        "pageSize": page_size,
        "date": validate_reference_date(reference_date),
    }


def encode_payload(payload):
    return base64.b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("utf-8")


def build_url(payload):
    return f"{B3_BASE_URL}referenceRatesProxy/Search/GetList/{encode_payload(payload)}"


def normalize_records(data):
    results = data.get("results")
    if results is None:
        raise ValueError("Resposta da B3 não contém o campo 'results'.")
    if not isinstance(results, list):
        raise ValueError("Campo 'results' da B3 não é uma lista.")
    records = []
    for item in results:
        try:
            records.append(
                RateRecord(
                    day252=int(item["day252"]),
                    day360=int(item["day360"]),
                    rate=str(item["rate"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Registro de taxa da B3 tem formato inesperado.") from exc
    return records


def fetch_reference_rates_page(
    reference_date,
    page_number=DEFAULT_PAGE_NUMBER,
    page_size=DEFAULT_PAGE_SIZE,
    opener=urllib.request.urlopen,
    timeout=30,
):
    payload = build_payload(
        reference_date,
        page_number=page_number,
        page_size=page_size,
    )
    url = build_url(payload)
    with opener(url, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    records = normalize_records(data)
    total_count = data.get("totalCount")
    return records, total_count


def fetch_reference_rates(
    reference_date,
    opener=urllib.request.urlopen,
    timeout=30,
    page_size=DEFAULT_PAGE_SIZE,
    max_pages=DEFAULT_MAX_PAGES,
    progress_callback=None,
):
    if page_size <= 0:
        raise ValueError("Tamanho da página deve ser maior que zero.")
    if max_pages <= 0:
        raise ValueError("Quantidade máxima de páginas deve ser maior que zero.")
    records = []
    total_pages = None
    for page_number in range(DEFAULT_PAGE_NUMBER, max_pages + 1):
        page_records, total_count = fetch_reference_rates_page(
            reference_date,
            page_number=page_number,
            page_size=page_size,
            opener=opener,
            timeout=timeout,
        )
        records.extend(page_records)
        if total_pages is None and total_count is not None and page_size > 0:
            total_pages = math.ceil(total_count / page_size)
        if progress_callback:
            progress_callback(page_number, total_pages)
        if len(page_records) < page_size:
            return records
    raise ValueError("Paginação da B3 excedeu o limite máximo de páginas.")


def fetch_rates_download(date_str):
    payload = {"language": "pt-br", "date": date_str, "id": "SLP"}
    compact = json.dumps(payload, separators=(",", ":"))
    encoded = base64.b64encode(compact.encode("utf-8")).decode("utf-8")
    url = f"{B3_BASE_URL}referenceRatesProxy/Search/GetDownloadFile/{encoded}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = resp.read()
    b64_text = raw.decode("latin-1").strip()
    if not b64_text:
        return []
    decoded = base64.b64decode(b64_text)
    text = decoded.decode("latin-1")
    lines = text.strip().split("\n")
    records = []
    for line in lines[1:]:
        parts = line.split(";")
        if len(parts) >= 4:
            records.append(RateRecord(
                day252=int(parts[1]),
                day360=int(parts[2]),
                rate=parts[3],
            ))
    return records


def fetch_historical_rates(base_date, progress_callback=None):
    from datetime import date
    today = date.today().isoformat()
    dates = [_days_ago(base_date, d) for d in EVOLUTION_DAYS]

    def fetch_one(date_str):
        if date_str == today:
            records = fetch_reference_rates(date_str, page_size=100)
        else:
            records = fetch_rates_download(date_str)
            if not records:
                records = fetch_reference_rates(date_str, page_size=100)
        return date_str, records

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_one, d): d for d in dates}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            date_str, records = future.result()
            results[date_str] = records
            if progress_callback:
                progress_callback(i + 1, len(dates))
    return results
