"""Asynchronous GLPI client."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import TYPE_CHECKING, Any

from glpikit.ai.policy import PolicyEngine
from glpikit.auth import (
    build_async_auth,
    build_authorization_url,
    generate_pkce_pair,
    resolve_mode,
)
from glpikit.errors import AuthenticationError, GLPIError, NotFoundError, PolicyViolationError
from glpikit.graphql import AsyncGraphQLClient
from glpikit.models import Document, Ticket, User
from glpikit.resources import (
    AsyncAppliancesResource,
    AsyncAssetsResource,
    AsyncCategoriesResource,
    AsyncChangesResource,
    AsyncComputersResource,
    AsyncContractsResource,
    AsyncDocumentsResource,
    AsyncEntitiesResource,
    AsyncFollowupsResource,
    AsyncGroupsResource,
    AsyncItemsResource,
    AsyncKnowledgebaseResource,
    AsyncLocationsResource,
    AsyncMassiveActionsResource,
    AsyncNetworkEquipmentResource,
    AsyncPrintersResource,
    AsyncProblemsResource,
    AsyncProfilesResource,
    AsyncProjectResource,
    AsyncRawResource,
    AsyncReservationsResource,
    AsyncSearchBuilder,
    AsyncSoftwareResource,
    AsyncSolutionsResource,
    AsyncSuppliersResource,
    AsyncTasksResource,
    AsyncTicketsResource,
    AsyncUsersResource,
)
from glpikit.transport import (
    AsyncTransport,
    MetricsCollector,
    RetryPolicy,
    build_observability_hooks,
)
from glpikit.utils import (
    TTLCache,
    extract_plugins,
    extract_plugins_from_itemtypes,
    summarize_capabilities,
)
from glpikit.v2 import AsyncV2Resources, infer_itemtypes_from_paths

if TYPE_CHECKING:
    from glpikit.resources.plugin import AsyncPluginItemsResource


class AsyncGLPI:
    def __init__(
        self,
        *,
        base_url: str,
        auth: dict[str, Any] | None = None,
        mode: str = "auto",
        api_version: str = "v2",
        oauth_token_path: str = "/api.php/oauth/token",
        timeout: float = 30.0,
        retry_policy: RetryPolicy | None = None,
        search_options_ttl: float = 300.0,
        headers: dict[str, str] | None = None,
        policy_engine: PolicyEngine | None = None,
        dry_run: bool = False,
        enable_observability: bool = False,
        enable_tracing: bool = False,
        metrics_collector: MetricsCollector | None = None,
        logger: logging.Logger | None = None,
        correlation_id_header: str = "X-Correlation-ID",
        transport: AsyncTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth or {}
        self._mode_preference = mode.lower().strip()
        self._auto_mode_enabled = self._mode_preference == "auto"
        self._fallback_attempted = False
        self._oauth_token_path = oauth_token_path
        self.mode = resolve_mode(mode, self.auth)
        self.engine = self.mode
        self.api_version = api_version
        self._search_options_cache: TTLCache[str, Any] = TTLCache(ttl_seconds=search_options_ttl)
        self._supports_graphql_cache: bool | None = None
        self._plugins_cache: list[str] | None = None
        self.policy_engine = policy_engine
        self.dry_run = dry_run

        default_headers = {
            "User-Agent": "glpikit/0.1.0",
            "Accept": "application/json",
            **(headers or {}),
        }
        if transport is None:
            request_hook = None
            response_hook = None
            if enable_observability:
                request_hook, response_hook = build_observability_hooks(
                    logger=logger,
                    metrics_collector=metrics_collector,
                    enable_tracing=enable_tracing,
                    correlation_id_header=correlation_id_header,
                )
            self.transport = AsyncTransport(
                base_url=self.base_url,
                timeout=timeout,
                retry_policy=retry_policy,
                headers=default_headers,
                request_hook=request_hook,
                response_hook=response_hook,
            )
        else:
            self.transport = transport

        self._auth = build_async_auth(self.mode, self.auth, token_path=oauth_token_path)

        self.raw = AsyncRawResource(self)
        self.items = AsyncItemsResource(self)
        self.tickets = AsyncTicketsResource(self)
        self.users = AsyncUsersResource(self)
        self.documents = AsyncDocumentsResource(self)
        self.massive_actions = AsyncMassiveActionsResource(self)
        self.groups = AsyncGroupsResource(self)
        self.entities = AsyncEntitiesResource(self)
        self.profiles = AsyncProfilesResource(self)
        self.knowledgebase = AsyncKnowledgebaseResource(self)
        self.problems = AsyncProblemsResource(self)
        self.changes = AsyncChangesResource(self)
        self.computers = AsyncComputersResource(self)
        self.printers = AsyncPrintersResource(self)
        self.network_equipment = AsyncNetworkEquipmentResource(self)
        self.software = AsyncSoftwareResource(self)
        self.contracts = AsyncContractsResource(self)
        self.suppliers = AsyncSuppliersResource(self)
        self.locations = AsyncLocationsResource(self)
        self.categories = AsyncCategoriesResource(self)
        self.followups = AsyncFollowupsResource(self)
        self.tasks = AsyncTasksResource(self)
        self.solutions = AsyncSolutionsResource(self)
        self.reservations = AsyncReservationsResource(self)
        self.project = AsyncProjectResource(self)
        self.appliances = AsyncAppliancesResource(self)
        self.assets = AsyncAssetsResource(self)
        self.v2 = AsyncV2Resources(self)
        self.graphql = AsyncGraphQLClient(self)

    @classmethod
    def from_env(cls, **kwargs: Any) -> "AsyncGLPI":
        base_url = os.getenv("GLPI_BASE_URL")
        if not base_url:
            raise ValueError("GLPI_BASE_URL is required")

        mode = os.getenv("GLPI_MODE", "auto")
        auth: dict[str, Any] = {}

        for key in (
            "GLPI_APP_TOKEN",
            "GLPI_USER_TOKEN",
            "GLPI_USERNAME",
            "GLPI_PASSWORD",
            "GLPI_CLIENT_ID",
            "GLPI_CLIENT_SECRET",
            "GLPI_REFRESH_TOKEN",
        ):
            value = os.getenv(key)
            if value:
                auth[key.replace("GLPI_", "").lower()] = value

        return cls(base_url=base_url, auth=auth, mode=mode, **kwargs)

    @classmethod
    def ai(cls, **kwargs: Any) -> "AsyncGLPI":
        retry_policy = kwargs.pop("retry_policy", RetryPolicy(max_attempts=4, backoff_factor=0.4))
        timeout = kwargs.pop("timeout", 45.0)
        return cls(retry_policy=retry_policy, timeout=timeout, **kwargs)

    @staticmethod
    def oauth_pkce_pair(length: int = 64) -> tuple[str, str]:
        return generate_pkce_pair(length)

    @staticmethod
    def oauth_authorization_url(
        *,
        authorize_url: str,
        client_id: str,
        redirect_uri: str,
        scope: str | None = None,
        state: str | None = None,
        code_challenge: str | None = None,
    ) -> str:
        return build_authorization_url(
            authorize_url=authorize_url,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
        )

    def capabilities(self, *, deep: bool = True) -> dict[str, Any]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.capabilities_async(deep=deep))

        openapi = self.v2._openapi if hasattr(self.v2, "_openapi") else None
        capabilities = summarize_capabilities(self, openapi=openapi)
        if hasattr(self.v2, "_operations"):
            capabilities["v2_operations"] = len(self.v2._operations)
        capabilities["supports_graphql"] = (
            self._supports_graphql_cache if self._supports_graphql_cache is not None else True
        )
        capabilities["plugins"] = list(self._plugins_cache or [])
        capabilities["auth_modes_available"] = [
            mode
            for mode, enabled in {
                "v1": self._has_v1_credentials(),
                "v2": self._has_v2_credentials(),
            }.items()
            if enabled
        ]
        known_itemtypes = sorted(
            key.split("::", maxsplit=1)[1]
            for key in self._search_options_cache.keys()
            if key.startswith("search_options::")
        )
        capabilities["known_itemtypes"] = known_itemtypes
        capabilities["plugin_itemtypes"] = [
            itemtype for itemtype in known_itemtypes if itemtype.lower().startswith("plugin")
        ]
        capabilities["itemtype_count"] = len(known_itemtypes)
        capabilities["plugin_count"] = len(capabilities["plugins"])
        return capabilities

    async def capabilities_async(self, *, deep: bool = True) -> dict[str, Any]:
        openapi: dict[str, Any] | None = None
        if self.mode == "v2" or deep:
            try:
                openapi = await self.v2.load_openapi()
            except Exception:
                openapi = None
        capabilities = summarize_capabilities(self, openapi=openapi)
        if self.mode == "v2":
            try:
                capabilities["v2_operations"] = len(await self.v2.operations())
            except Exception:
                pass
        capabilities["supports_graphql"] = await self.supports_graphql_async(refresh=deep)
        capabilities["supports_v2"] = await self.supports_v2_async(probe=deep)
        capabilities["plugins"] = await self.discover_plugins(refresh=deep)
        capabilities["auth_modes_available"] = [
            mode
            for mode, enabled in {
                "v1": self._has_v1_credentials(),
                "v2": self._has_v2_credentials(),
            }.items()
            if enabled
        ]
        known_itemtypes = await self.discover_itemtypes(probe_common=deep)
        capabilities["known_itemtypes"] = known_itemtypes
        capabilities["plugin_itemtypes"] = [
            itemtype for itemtype in known_itemtypes if itemtype.lower().startswith("plugin")
        ]
        capabilities["itemtype_count"] = len(known_itemtypes)
        capabilities["plugin_count"] = len(capabilities["plugins"])
        return capabilities

    def supports_graphql(self) -> bool:
        return self._supports_graphql_cache if self._supports_graphql_cache is not None else True

    async def supports_graphql_async(self, *, refresh: bool = False) -> bool:
        if self._supports_graphql_cache is not None and not refresh:
            return self._supports_graphql_cache
        supported = await self._probe_graphql_support()
        self._supports_graphql_cache = supported
        return supported

    def supports_v2(self, *, probe: bool = False) -> bool:
        if self.mode == "v2":
            return True
        if not probe:
            return False
        return self.v2._openapi is not None and bool(self.v2._openapi)

    async def supports_v2_async(self, *, probe: bool = False) -> bool:
        if self.mode == "v2":
            return True
        if not probe:
            return False
        try:
            openapi = await self.v2.load_openapi(force_refresh=True)
            return bool(openapi)
        except Exception:
            return False

    def supports_itemtype(self, _itemtype: str) -> bool:
        if self.mode == "v2" and self.v2._openapi is not None:
            known = {entry.lower() for entry in infer_itemtypes_from_paths(self.v2._openapi)}
            return _itemtype.lower() in known
        cache_key = f"search_options::{_itemtype.lower()}"
        return cache_key in self._search_options_cache.keys()

    async def supports_itemtype_async(self, itemtype: str) -> bool:
        if self.mode == "v2":
            try:
                openapi = await self.v2.load_openapi()
                known = {entry.lower() for entry in infer_itemtypes_from_paths(openapi)}
                if known:
                    return itemtype.lower() in known
            except Exception:
                pass

        try:
            await self.items.list_search_options(itemtype)
            return True
        except Exception:
            return False

    def search(self, itemtype: str) -> AsyncSearchBuilder:
        return AsyncSearchBuilder(self, itemtype)

    async def search_options(self, itemtype: str) -> Any:
        return await self.items.list_search_options(itemtype)

    async def discover_plugins(self, *, refresh: bool = False) -> list[str]:
        if self._plugins_cache is not None and not refresh:
            return list(self._plugins_cache)
        if self.mode == "v2":
            try:
                openapi = await self.v2.load_openapi()
                plugins = extract_plugins_from_itemtypes(infer_itemtypes_from_paths(openapi))
                self._plugins_cache = list(plugins)
                return plugins
            except Exception:
                return []
        if self.mode != "v1":
            return []
        try:
            config = await self.raw.get("/apirest.php/getGlpiConfig")
        except Exception:
            return []
        plugins = extract_plugins(config)
        self._plugins_cache = list(plugins)
        return plugins

    async def discover_itemtypes(self, *, probe_common: bool = False) -> list[str]:
        names: set[str] = set()
        if self.mode == "v2":
            try:
                openapi = await self.v2.load_openapi()
                names.update(infer_itemtypes_from_paths(openapi))
            except Exception:
                pass
        for key in self._search_options_cache.keys():
            if key.startswith("search_options::"):
                names.add(key.split("::", maxsplit=1)[1])
        if self.mode == "v1" and probe_common:
            common_itemtypes = (
                "Ticket",
                "User",
                "Group",
                "Entity",
                "Profile",
                "Computer",
                "Document",
                "Problem",
                "Change",
                "Project",
                "Supplier",
            )
            for itemtype in common_itemtypes:
                try:
                    await self.items.list_search_options(itemtype)
                    names.add(itemtype)
                except Exception:
                    continue
        return sorted(names)

    def plugin(self, itemtype: str) -> AsyncPluginItemsResource:
        from glpikit.resources.plugin import AsyncPluginItemsResource

        return AsyncPluginItemsResource(self, itemtype)

    def v2_itemtype(self, itemtype: str) -> Any:
        return self.v2.adapter(itemtype)

    def set_policy_engine(self, policy_engine: PolicyEngine | None) -> None:
        self.policy_engine = policy_engine

    def _has_v1_credentials(self) -> bool:
        return bool(
            self.auth.get("user_token")
            or self.auth.get("app_token")
            or (self.auth.get("username") and self.auth.get("password"))
        )

    def _has_v2_credentials(self) -> bool:
        oauth_hints = (
            "client_id",
            "client_secret",
            "refresh_token",
            "authorization_code",
            "code",
            "code_verifier",
        )
        if any(self.auth.get(key) for key in oauth_hints):
            return True
        if self.auth.get("grant_type"):
            return True
        return bool(self.auth.get("username") and self.auth.get("password"))

    def _fallback_modes(self) -> list[str]:
        modes: list[str] = []
        if self.mode == "v2" and self._has_v1_credentials():
            modes.append("v1")
        if self.mode == "v1" and self._has_v2_credentials():
            modes.append("v2")
        return modes

    def _remap_path_for_mode(self, path: str, *, from_mode: str, to_mode: str) -> str:
        if from_mode == to_mode:
            return path
        v1_prefix = "/apirest.php/"
        v2_prefix = f"/api.php/{self.api_version}/"
        if from_mode == "v2" and to_mode == "v1" and path.startswith(v2_prefix):
            return f"{v1_prefix}{path[len(v2_prefix):]}"
        if from_mode == "v1" and to_mode == "v2" and path.startswith(v1_prefix):
            return f"{v2_prefix}{path[len(v1_prefix):]}"
        return path

    async def _attempt_auth_fallback(self) -> bool:
        if not self._auto_mode_enabled or self._fallback_attempted:
            return False

        self._fallback_attempted = True
        for candidate in self._fallback_modes():
            candidate_auth = build_async_auth(
                candidate,
                self.auth,
                token_path=self._oauth_token_path,
            )
            try:
                await candidate_auth.prepare(self.transport)
            except Exception:
                continue

            try:
                await self._auth.close(self.transport)
            except Exception:
                pass
            self.mode = candidate
            self.engine = candidate
            self._auth = candidate_auth
            self._supports_graphql_cache = None
            self._plugins_cache = None
            return True
        return False

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
        skip_auth: bool = False,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        requested_mode = self.mode
        merged_headers = dict(headers or {})

        if not skip_auth and self.policy_engine is not None:
            decision = self.policy_engine.evaluate(
                method=method,
                path=path,
                confirmed=confirmed,
                dry_run=self.dry_run if dry_run is None else dry_run,
                payload=json if json is not None else data,
            )
            if not decision.allowed:
                raise PolicyViolationError(
                    decision.reason or "operation blocked by policy",
                    payload={"method": method, "path": path},
                )
            if decision.dry_run:
                return {
                    "dry_run": True,
                    "method": method,
                    "path": path,
                    "params": params,
                    "json": json,
                    "data": data,
                }

        if not skip_auth:
            try:
                await self._auth.prepare(self.transport)
            except (AuthenticationError, GLPIError):
                if not await self._attempt_auth_fallback():
                    raise
            if self.mode != requested_mode:
                path = self._remap_path_for_mode(path, from_mode=requested_mode, to_mode=self.mode)
                requested_mode = self.mode
            merged_headers = {**self._auth.headers(), **merged_headers}

        response = await self.transport.request_raw(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=merged_headers,
        )

        if response.status_code == 401 and not skip_auth:
            retry_mode = self.mode
            try:
                refreshed = await self._auth.on_unauthorized(self.transport)
            except (AuthenticationError, GLPIError):
                refreshed = False
            if refreshed:
                retry_headers = {**self._auth.headers(), **(headers or {})}
                response = await self.transport.request_raw(
                    method,
                    path,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=retry_headers,
                )
                if response.status_code == 401 and await self._attempt_auth_fallback():
                    path = self._remap_path_for_mode(path, from_mode=retry_mode, to_mode=self.mode)
                    retry_headers = {**self._auth.headers(), **(headers or {})}
                    response = await self.transport.request_raw(
                        method,
                        path,
                        params=params,
                        json=json,
                        data=data,
                        files=files,
                        headers=retry_headers,
                    )
            elif await self._attempt_auth_fallback():
                path = self._remap_path_for_mode(path, from_mode=retry_mode, to_mode=self.mode)
                retry_headers = {**self._auth.headers(), **(headers or {})}
                response = await self.transport.request_raw(
                    method,
                    path,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=retry_headers,
                )

        return self.transport.parse_response(response)

    def _collection_prefix(self) -> str:
        if self.mode == "v1":
            return "/apirest.php"
        return f"/api.php/{self.api_version}"

    def _item_collection_path(self, itemtype: str) -> str:
        return f"{self._collection_prefix()}/{itemtype}"

    def _item_path(self, itemtype: str, item_id: int) -> str:
        return f"{self._collection_prefix()}/{itemtype}/{item_id}"

    def _subitem_path(self, itemtype: str, item_id: int, sub_itemtype: str) -> str:
        return f"{self._collection_prefix()}/{itemtype}/{item_id}/{sub_itemtype}"

    def _search_options_path(self, itemtype: str) -> str:
        if self.mode == "v1":
            return f"/apirest.php/listSearchOptions/{itemtype}"
        return f"{self._collection_prefix()}/{itemtype}/searchOptions"

    def _search_path(self, itemtype: str) -> str:
        if self.mode == "v1":
            return f"/apirest.php/search/{itemtype}"
        return f"{self._collection_prefix()}/search/{itemtype}"

    def _document_upload_path(self) -> str:
        return self._item_collection_path("Document")

    def _document_download_path(self, document_id: int) -> str:
        return self._item_path("Document", document_id)

    def _user_picture_path(self, user_id: int) -> str:
        return self._subitem_path("User", user_id, "Picture")

    def _graphql_path(self) -> str:
        return "/api.php/GraphQL"

    async def _probe_graphql_support(self) -> bool:
        try:
            await self._request(
                "POST",
                self._graphql_path(),
                json={"query": "query { __typename }"},
            )
            return True
        except NotFoundError:
            return False
        except GLPIError as exc:
            return exc.status_code in {400, 401, 403, 405}
        except Exception:
            return False

    def _to_upload_manifest(self, payload: dict[str, Any]) -> str:
        return json.dumps({"input": payload}, ensure_ascii=True)

    def _coerce_item(self, itemtype: str, payload: Any) -> Any:
        model_map = {
            "Ticket": Ticket,
            "User": User,
            "Document": Document,
        }
        model = model_map.get(itemtype)
        if not model or not isinstance(payload, dict):
            return payload

        if isinstance(payload.get("data"), dict):
            payload = payload["data"]
        if isinstance(payload.get("input"), dict):
            payload = payload["input"]

        try:
            return model.model_validate(payload)
        except Exception:
            return payload

    async def close(self) -> None:
        try:
            await self._auth.close(self.transport)
        except AuthenticationError:
            pass
        finally:
            await self.transport.close()

    async def __aenter__(self) -> "AsyncGLPI":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
