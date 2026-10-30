"""Descoberta CKAN dos recursos do Tesouro Direto."""

from __future__ import annotations

import urllib.parse

from b3_selic_pre.application.tesouro import (
    RESGATE_KEYS,
    TesouroDataError,
    normalizar_texto,
    resource_spec,
)
from b3_selic_pre.application.tesouro._resources import TesouroResourceSpec
from b3_selic_pre.domain.constants import (
    TESOURO_CKAN_BASE_URL,
    TESOURO_DATASET_NAME,
)
from b3_selic_pre.infrastructure.tesouro_types import TesouroResource


class TesouroDiscoveryMixin:
    """Métodos de descoberta compartilhados pelo cliente CKAN."""

    def _fetch_json(
        self: TesouroDiscoveryMixin, url: str
    ) -> dict[str, object]:
        """Return the CKAN JSON payload; implemented by the client."""
        raise NotImplementedError

    def _package_result(
        self: TesouroDiscoveryMixin, dataset_name: str
    ) -> dict[str, object]:
        url = (
            f"{TESOURO_CKAN_BASE_URL}/api/3/action/package_show"
            f"?id={urllib.parse.quote(dataset_name)}"
        )
        payload = self._fetch_json(url)
        result = payload.get("result")
        if not isinstance(result, dict):
            raise TesouroDataError("Resposta CKAN sem o objeto 'result'.")
        return result

    def discover(self: TesouroDiscoveryMixin) -> TesouroResource:
        """Discover the sales dataset and its single CSV resource."""
        return self._resource_from_result(
            self._package_result(TESOURO_DATASET_NAME)
        )

    def discover_resource(
        self: TesouroDiscoveryMixin, key: str
    ) -> TesouroResource:
        """Discover one logical resource by its registry key."""
        spec = resource_spec(key)
        result = self._package_result(spec.dataset_name)
        return self._select_named(result, spec, select_latest=key == "cupom")

    def discover_resgates(
        self: TesouroDiscoveryMixin,
    ) -> dict[str, TesouroResource]:
        """Discover the three logical redemption resources."""
        result = self._package_result(
            resource_spec(RESGATE_KEYS[0]).dataset_name
        )
        return {
            key: self._select_named(
                result, resource_spec(key), select_latest=key == "cupom"
            )
            for key in RESGATE_KEYS
        }

    def discover_estoque(self: TesouroDiscoveryMixin) -> TesouroResource:
        """Discover the monthly stock CSV resource."""
        return self.discover_resource("estoque")

    @staticmethod
    def _csv_resource(result: dict[str, object]) -> dict[str, object]:
        resources = result.get("resources")
        if not isinstance(resources, list):
            raise TesouroDataError("Dataset do Tesouro sem lista de recursos.")
        csv_resources = [
            resource
            for resource in resources
            if isinstance(resource, dict)
            and str(resource.get("format", "")).upper() == "CSV"
        ]
        if len(csv_resources) != 1:
            raise TesouroDataError(
                "Dataset do Tesouro deve ter exatamente um recurso CSV."
            )
        return csv_resources[0]

    @staticmethod
    def _resource_url(resource: dict[str, object]) -> str:
        url = resource.get("url")
        if not isinstance(url, str) or not url:
            raise TesouroDataError("Recurso CSV do Tesouro sem URL.")
        return url

    @staticmethod
    def _csv_resources(result: dict[str, object]) -> list[dict[str, object]]:
        resources = result.get("resources")
        if not isinstance(resources, list):
            raise TesouroDataError("Dataset do Tesouro sem lista de recursos.")
        return [
            resource
            for resource in resources
            if isinstance(resource, dict)
            and str(resource.get("format", "")).upper() == "CSV"
        ]

    @staticmethod
    def _matches(resource: dict[str, object], spec: TesouroResourceSpec) -> bool:
        def token(value: str) -> str:
            cleaned = value.replace("-", " ").replace("_", " ")
            return normalizar_texto(cleaned)

        expected = token(spec.resource_name)
        name = token(str(resource.get("name") or ""))
        url = str(resource.get("url") or "")
        filename = token(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])
        return expected in name or expected in filename

    @staticmethod
    def _resource(
        result: dict[str, object], resource: dict[str, object]
    ) -> TesouroResource:
        return TesouroResource(
            dataset_name=str(result.get("name") or ""),
            dataset_id=str(result.get("id") or ""),
            resource_id=str(resource.get("id") or ""),
            resource_url=TesouroDiscoveryMixin._resource_url(resource),
            last_modified=resource.get("last_modified"),
        )

    @staticmethod
    def _select_named(
        result: dict[str, object],
        spec: TesouroResourceSpec,
        *,
        select_latest: bool = False,
    ) -> TesouroResource:
        candidates = [
            resource
            for resource in TesouroDiscoveryMixin._csv_resources(result)
            if TesouroDiscoveryMixin._matches(resource, spec)
        ]
        if not candidates:
            raise TesouroDataError(
                f"Recurso CSV ausente no dataset do Tesouro: {spec.resource_name}."
            )
        if len(candidates) == 1:
            return TesouroDiscoveryMixin._resource(result, candidates[0])
        if not select_latest:
            raise TesouroDataError(
                f"Recurso CSV ambíguo no dataset do Tesouro: {spec.resource_name}."
            )
        ordered = sorted(
            candidates,
            key=lambda item: str(item.get("last_modified") or ""),
            reverse=True,
        )
        if str(ordered[0].get("last_modified") or "") == str(
            ordered[1].get("last_modified") or ""
        ):
            raise TesouroDataError(
                f"Recurso CSV ambíguo no dataset do Tesouro: {spec.resource_name}."
            )
        return TesouroDiscoveryMixin._resource(result, ordered[0])

    @staticmethod
    def _resource_from_result(result: dict[str, object]) -> TesouroResource:
        resource = TesouroDiscoveryMixin._csv_resource(result)
        return TesouroResource(
            dataset_name=str(result.get("name") or TESOURO_DATASET_NAME),
            dataset_id=str(result.get("id") or ""),
            resource_id=str(resource.get("id") or ""),
            resource_url=TesouroDiscoveryMixin._resource_url(resource),
            last_modified=resource.get("last_modified"),
        )
