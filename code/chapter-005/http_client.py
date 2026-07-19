"""Synchronous platform HTTP client."""

from __future__ import annotations

import time
import uuid
from typing import Any, Iterator, Mapping

import httpx

from json_codec import dumps
from models import AuthConfig, RequestSpec, ResponseEnvelope
from rate_limit import TokenBucket
from retry import RetryPolicy


class HttpClientError(RuntimeError):
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


class HttpClient:
    def __init__(
        self,
        *,
        base_url: str = "",
        auth: AuthConfig | None = None,
        default_headers: Mapping[str, str] | None = None,
        rate_limiter: TokenBucket | None = None,
        retry: RetryPolicy | None = None,
        user_agent: str = "ai-agent-platform/0.1",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth or AuthConfig()
        self.default_headers = dict(default_headers or {})
        self.default_headers.setdefault("User-Agent", user_agent)
        self.default_headers.setdefault("Accept", "application/json")
        self.rate_limiter = rate_limiter
        self.retry = retry or RetryPolicy()
        self._transport = transport

    def _url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        if not self.base_url:
            return path_or_url
        return f"{self.base_url}/{path_or_url.lstrip('/')}"

    def _build_headers(self, spec: RequestSpec, request_id: str) -> dict[str, str]:
        return {
            **self.default_headers,
            **self.auth.headers(),
            **dict(spec.headers),
            "X-Request-ID": request_id,
        }

    def request(self, spec: RequestSpec) -> ResponseEnvelope:
        url = self._url(spec.url)
        request_id = str(uuid.uuid4())
        headers = self._build_headers(spec, request_id)
        content: bytes | None = None
        if spec.json_body is not None:
            content = dumps(spec.json_body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        attempt = 0
        last_error: Exception | None = None
        while True:
            attempt += 1
            if self.rate_limiter:
                self.rate_limiter.acquire(1.0)
            started = time.perf_counter()
            try:
                with httpx.Client(timeout=spec.timeout_s, transport=self._transport) as client:
                    response = client.request(
                        spec.method.upper(),
                        url,
                        headers=headers,
                        content=content,
                        params=spec.params,
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
                        retry_after = _parse_retry_after(envelope.headers.get("retry-after"))
                        time.sleep(self.retry.delay_s(attempt, retry_after))
                        continue
                    raise HttpClientError(
                        f"HTTP {response.status_code} for {spec.method} {url}",
                        status_code=response.status_code,
                        request_id=request_id,
                    )
                return envelope
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
                last_error = exc
                if not self.retry.allow(spec.method, None, spec.idempotent, attempt):
                    raise HttpClientError(
                        f"network failure for {spec.method} {url}: {exc}",
                        request_id=request_id,
                    ) from exc
                time.sleep(self.retry.delay_s(attempt))

        raise HttpClientError(f"exhausted retries: {last_error}", request_id=request_id)

    def get_json(self, path: str, **kwargs: Any) -> Any:
        timeout_s = float(kwargs.pop("timeout_s", 30.0))
        headers = kwargs.pop("headers", {})
        params = kwargs.pop("params", None)
        env = self.request(
            RequestSpec(
                method="GET",
                url=path,
                idempotent=True,
                timeout_s=timeout_s,
                headers=headers,
                params=params,
            )
        )
        return env.json()

    def post_json(
        self,
        path: str,
        body: Any,
        *,
        idempotent: bool = False,
        **kwargs: Any,
    ) -> Any:
        timeout_s = float(kwargs.pop("timeout_s", 30.0))
        headers = kwargs.pop("headers", {})
        env = self.request(
            RequestSpec(
                method="POST",
                url=path,
                json_body=body,
                idempotent=idempotent,
                timeout_s=timeout_s,
                headers=headers,
            )
        )
        return env.json()

    def stream_lines(self, spec: RequestSpec) -> Iterator[str]:
        url = self._url(spec.url)
        request_id = str(uuid.uuid4())
        headers = self._build_headers(spec, request_id)
        headers.setdefault("Accept", "text/event-stream")
        if self.rate_limiter:
            self.rate_limiter.acquire(1.0)
        with httpx.Client(timeout=spec.timeout_s, transport=self._transport) as client:
            with client.stream(
                spec.method.upper(),
                url,
                headers=headers,
                params=spec.params,
            ) as resp:
                if resp.status_code >= 400:
                    raise HttpClientError(
                        f"HTTP {resp.status_code} streaming {url}",
                        status_code=resp.status_code,
                        request_id=request_id,
                    )
                for line in resp.iter_lines():
                    yield line


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
