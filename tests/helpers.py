from __future__ import annotations

import httpx
import pytest


class FakeResponse:
    def __init__(
        self,
        payload: str,
        *,
        request_url: str,
        status_code: int = 200,
    ):
        self.text = payload
        self.status_code = status_code
        self.request = httpx.Request("GET", request_url)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=self.request,
                response=httpx.Response(self.status_code, request=self.request),
            )

    def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeAsyncClient:
    def __init__(
        self,
        response: FakeResponse | None = None,
        error: Exception | None = None,
        calls: list[dict[str, object]] | None = None,
        **_kwargs,
    ):
        self._response = response
        self._error = error
        self._calls = calls if calls is not None else []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, params: dict[str, object] | None = None) -> FakeResponse:
        self._calls.append({"url": url, "params": params})
        if self._error is not None:
            raise self._error
        if self._response is None:
            raise AssertionError("Fake client was called without a configured response")
        return self._response


def mock_async_client_response(
    monkeypatch: pytest.MonkeyPatch,
    *,
    target: str,
    request_url: str,
    payload: str | None = None,
    status_code: int = 200,
    error: Exception | None = None,
    calls: list[dict[str, object]] | None = None,
) -> None:
    def _fake_async_client(*_args, **_kwargs):
        response = (
            FakeResponse(payload, request_url=request_url, status_code=status_code)
            if payload is not None
            else None
        )
        return FakeAsyncClient(response=response, error=error, calls=calls)

    monkeypatch.setattr(target, _fake_async_client)


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name: str | None = None):
        def _decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func

        return _decorator
