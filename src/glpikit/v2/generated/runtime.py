"""Runtime-generated accessors for OpenAPI operation ids."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    from glpikit.v2.resources import AsyncV2Resources, V2Resources


class V2GeneratedClient:
    """Exposes OpenAPI `operationId`s as dynamic callables.

    Example:
        glpi.v2.generated.getTicket(id=123)
    """

    def __init__(
        self,
        resources: V2Resources,
        *,
        typed: bool = False,
        validate_request: bool = True,
    ) -> None:
        self._resources = resources
        self._typed_default = typed
        self._validate_request_default = validate_request
        self._operations_cache: set[str] | None = None

    def refresh(self) -> "V2GeneratedClient":
        self._resources.load_openapi(force_refresh=True)
        self._operations_cache = set(self._resources.operations())
        return self

    def operations(self) -> list[str]:
        operations = self._resources.operations()
        self._operations_cache = set(operations)
        return operations

    def has(self, operation_id: str) -> bool:
        if self._operations_cache is None:
            self.operations()
        assert self._operations_cache is not None
        return operation_id in self._operations_cache

    def input_model(self, operation_id: str) -> type[Any] | None:
        return self._resources.request_model(operation_id)

    def output_model(self, operation_id: str) -> type[Any] | Any:
        self._resources.load_openapi()
        return self._resources._response_models.get(operation_id)  # noqa: SLF001

    def call(
        self,
        operation_id: str,
        *,
        typed: bool | None = None,
        validate_request: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        use_typed = self._typed_default if typed is None else typed
        use_validation = (
            self._validate_request_default if validate_request is None else validate_request
        )
        if use_typed:
            return self._resources.call_typed(
                operation_id,
                validate_request=use_validation,
                **kwargs,
            )
        return self._resources.call(
            operation_id,
            validate_request=use_validation,
            **kwargs,
        )

    def operation(
        self,
        operation_id: str,
        *,
        typed: bool | None = None,
        validate_request: bool | None = None,
    ) -> Callable[..., Any]:
        if not self.has(operation_id):
            raise AttributeError(f"Unknown operation_id: {operation_id}")

        def _caller(**kwargs: Any) -> Any:
            return self.call(
                operation_id,
                typed=typed,
                validate_request=validate_request,
                **kwargs,
            )

        _caller.__name__ = operation_id
        return _caller

    def __getattr__(self, name: str) -> Callable[..., Any]:
        return self.operation(name)


class AsyncV2GeneratedClient:
    """Async counterpart of :class:`V2GeneratedClient`."""

    def __init__(
        self,
        resources: AsyncV2Resources,
        *,
        typed: bool = False,
        validate_request: bool = True,
    ) -> None:
        self._resources = resources
        self._typed_default = typed
        self._validate_request_default = validate_request
        self._operations_cache: set[str] | None = None

    async def refresh(self) -> "AsyncV2GeneratedClient":
        await self._resources.load_openapi(force_refresh=True)
        self._operations_cache = set(await self._resources.operations())
        return self

    async def operations(self) -> list[str]:
        operations = await self._resources.operations()
        self._operations_cache = set(operations)
        return operations

    async def has(self, operation_id: str) -> bool:
        if self._operations_cache is None:
            await self.operations()
        assert self._operations_cache is not None
        return operation_id in self._operations_cache

    async def input_model(self, operation_id: str) -> type[Any] | None:
        return await self._resources.request_model(operation_id)

    async def output_model(self, operation_id: str) -> type[Any] | Any:
        await self._resources.load_openapi()
        return self._resources._response_models.get(operation_id)  # noqa: SLF001

    async def call(
        self,
        operation_id: str,
        *,
        typed: bool | None = None,
        validate_request: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        use_typed = self._typed_default if typed is None else typed
        use_validation = (
            self._validate_request_default if validate_request is None else validate_request
        )
        if use_typed:
            return await self._resources.call_typed(
                operation_id,
                validate_request=use_validation,
                **kwargs,
            )
        return await self._resources.call(
            operation_id,
            validate_request=use_validation,
            **kwargs,
        )

    def operation(
        self,
        operation_id: str,
        *,
        typed: bool | None = None,
        validate_request: bool | None = None,
    ) -> Callable[..., Awaitable[Any]]:
        async def _caller(**kwargs: Any) -> Any:
            if not await self.has(operation_id):
                raise AttributeError(f"Unknown operation_id: {operation_id}")
            return await self.call(
                operation_id,
                typed=typed,
                validate_request=validate_request,
                **kwargs,
            )

        _caller.__name__ = operation_id
        return _caller

    def __getattr__(self, name: str) -> Callable[..., Awaitable[Any]]:
        return self.operation(name)
