"""Async platform HTTP client."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Mapping

import httpx

from models import RequestSpec, ResponseEnvelope
from rate_limit_async import AsyncTokenBucket
from retry import RetryPolicy


class AsyncHttpClientError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id


class AsyncHttpClient:
    def __init__(
        self,
        *,
        base_url: str = "",
        default_headers: Mapping[str, str] | None = None,
        rate_limiter: AsyncTokenBucket | None = None,
        retry: RetryPolicy | None = None,
        timeout_s: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
        user_agent: str = "ai-agent-platform-async/0.1",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        headers = dict(default_headers or {})
        headers.setdefault("User-Agent", user_agent)
        headers.setdefault("Accept", "application/json")
        self.default_headers = headers
        self.rate_limiter = rate_limiter
        self.retry = retry or RetryPolicy()
        self._client = httpx.AsyncClient(
            timeout=timeout_s,
            transport=transport,
            headers=self.default_headers,
        )

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    def _url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        if not self.base_url:
            return path_or_url
        return f"{self.base_url}/{path_or_url.lstrip('/')}"

    async def request(self, spec: RequestSpec) -> ResponseEnvelope:
        url = self._url(spec.url)
        request_id = str(uuid.uuid4())
        headers = {
            **self.default_headers,
            **dict(spec.headers),
            "X-Request-ID": request_id,
        }
        content: bytes | None = None
        if spec.json_body is not None:
            content = json.dumps(spec.json_body, ensure_ascii=False).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        attempt = 0
        last_error: Exception | None = None
        while True:
            attempt += 1
            if self.rate_limiter:
                await self.rate_limiter.acquire(1.0)
            started = time.perf_counter()
            try:
                response = await self._client.request(
                    spec.method.upper(),
                    url,
                    headers=headers,
                    content=content,
                    params=spec.params,
                    timeout=spec.timeout_s,
                )
                elapsed = time.perf_counter() - started
                envelope = ResponseEnvelope(
                    status_code=response.status_code,
                    headers={k.lower(): v for k, v in response.headers.items()},
                    body_text=response.text,
                    request_id=request_id,
                    elapsed_s=elapsed,
                )
                if response.status_code >= 400:
                    if self.retry.allow(
                        spec.method, response.status_code, spec.idempotent, attempt
                    ):
                        retry_after = _parse_retry_after(
                            envelope.headers.get("retry-after")
                        )
                        await asyncio.sleep(self.retry.delay_s(attempt, retry_after))
                        continue
                    raise AsyncHttpClientError(
                        f"HTTP {response.status_code} for {spec.method} {url}",
                        status_code=response.status_code,
                        request_id=request_id,
                    )
                return envelope
            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
            ) as exc:
                last_error = exc
                if not self.retry.allow(spec.method, None, spec.idempotent, attempt):
                    raise AsyncHttpClientError(
                        f"network failure for {spec.method} {url}: {exc}",
                        request_id=request_id,
                    ) from exc
                await asyncio.sleep(self.retry.delay_s(attempt))

        raise AsyncHttpClientError(
            f"exhausted retries: {last_error}", request_id=request_id
        )

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        timeout_s = float(kwargs.pop("timeout_s", 30.0))
        env = await self.request(
            RequestSpec(method="GET", url=url, idempotent=True, timeout_s=timeout_s)
        )
        return env.json()

    async def post_json(
        self, url: str, body: Any, *, idempotent: bool = False, **kwargs: Any
    ) -> Any:
        timeout_s = float(kwargs.pop("timeout_s", 30.0))
        env = await self.request(
            RequestSpec(
                method="POST",
                url=url,
                json_body=body,
                idempotent=idempotent,
                timeout_s=timeout_s,
            )
        )
        return env.json()


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
