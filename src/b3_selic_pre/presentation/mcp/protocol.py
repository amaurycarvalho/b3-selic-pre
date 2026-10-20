"""Constantes, validação e envelopes JSON-RPC da revisão MCP 2026-07-28."""

from __future__ import annotations

import json

from b3_selic_pre import __version__

PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_VERSIONS = (PROTOCOL_VERSION,)
SERVER_NAME = "b3-selic-pre"

META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_CLIENT_INFO = "io.modelcontextprotocol/clientInfo"
META_CAPABILITIES = "io.modelcontextprotocol/clientCapabilities"
META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
UNSUPPORTED_PROTOCOL_VERSION = -32022


class JsonRpcError(Exception):
    """Erro JSON-RPC com código, mensagem e dados opcionais."""

    def __init__(
        self: JsonRpcError,
        code: int,
        message: str,
        data: dict[str, object] | None = None,
    ) -> None:
        """Crie um erro JSON-RPC com código, mensagem e dados opcionais."""
        super().__init__(code, message, data)
        self.code = code
        self.message = message
        self.data = data


class InvalidParams(JsonRpcError):
    """Parâmetros de requisição inválidos (JSON-RPC -32602)."""

    def __init__(self: InvalidParams, message: str) -> None:  # noqa: B042
        """Crie um erro de parâmetros inválidos."""
        super().__init__(INVALID_PARAMS, message, None)


def server_info() -> dict[str, str]:
    """Return the server identity advertised in results."""
    return {"name": SERVER_NAME, "version": __version__}


def require_meta(params: object) -> str:
    """Validate required per-request metadata and return the version."""
    if not isinstance(params, dict):
        raise InvalidParams("params deve ser um objeto")
    meta = params.get("_meta")
    if not isinstance(meta, dict):
        raise InvalidParams("_meta obrigatório")
    version = meta.get(META_VERSION)
    capabilities = meta.get(META_CAPABILITIES)
    if not isinstance(version, str):
        raise InvalidParams(f"_meta.{META_VERSION} obrigatório")
    if not isinstance(capabilities, dict):
        raise InvalidParams(f"_meta.{META_CAPABILITIES} obrigatório")
    return version


def ensure_supported_version(version: str) -> None:
    """Raise UnsupportedProtocolVersionError when ``version`` is not supported."""
    if version not in SUPPORTED_VERSIONS:
        raise JsonRpcError(
            UNSUPPORTED_PROTOCOL_VERSION,
            "Unsupported protocol version",
            {
                "supported": list(SUPPORTED_VERSIONS),
                "requested": version,
            },
        )


def validate_meta(params: object) -> str:
    """Validate metadata and protocol version for a modern request."""
    version = require_meta(params)
    ensure_supported_version(version)
    return version


def initialize_error() -> JsonRpcError:
    """Return the error used to reject the legacy ``initialize`` handshake."""
    supported = ", ".join(SUPPORTED_VERSIONS)
    return JsonRpcError(
        METHOD_NOT_FOUND,
        f"initialize não é suportado; versões suportadas: {supported}. "
        "Use server/discover.",
        {"supported": list(SUPPORTED_VERSIONS)},
    )


def result(payload: dict[str, object]) -> dict[str, object]:
    """Wrap a payload in a complete MCP result with server identity."""
    envelope = {"resultType": "complete"}
    envelope.update(payload)
    meta = envelope.setdefault("_meta", {})
    if isinstance(meta, dict):
        meta[META_SERVER_INFO] = server_info()
    return envelope


def tool_result(
    payload: dict[str, object],
    is_error: bool = False,
) -> dict[str, object]:
    """Build a ``tools/call`` result with structured and text content."""
    text = json.dumps(payload, ensure_ascii=False)
    envelope: dict[str, object] = {
        "resultType": "complete",
        "content": [{"type": "text", "text": text}],
        "structuredContent": payload,
        "_meta": {META_SERVER_INFO: server_info()},
    }
    if is_error:
        envelope["isError"] = True
    return envelope


def error_response(
    request_id: object,
    code: int,
    message: str,
    data: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a JSON-RPC error response."""
    error: dict[str, object] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error,
    }


def success_response(
    request_id: object,
    payload: dict[str, object],
) -> dict[str, object]:
    """Build a JSON-RPC success response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": payload,
    }


def discover_result(instructions: str) -> dict[str, object]:
    """Build the mandatory ``server/discover`` result."""
    return result(
        {
            "supportedVersions": list(SUPPORTED_VERSIONS),
            "capabilities": {"tools": {}},
            "instructions": instructions,
            "ttlMs": 3_600_000,
            "cacheScope": "public",
        }
    )
