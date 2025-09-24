"""Ollama service for OpenGov Food."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import AsyncRetrying, RetryError, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..core.config import get_settings

logger = structlog.get_logger(__name__)


class OllamaService:
    """Service for managing Ollama LLM operations."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        if not self.base_url:
            raise ValueError("Ollama base URL is not configured")

        async def _execute_request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.request(method, f"{self.base_url}{path}", **kwargs)
                response.raise_for_status()
                return response

        retry_policy = AsyncRetrying(
            retry=retry_if_exception_type(httpx.HTTPError),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            stop=stop_after_attempt(3),
            reraise=True,
        )

        try:
            async for attempt in retry_policy:  # pragma: no cover - retry loop
                with attempt:
                    return await _execute_request()
        except RetryError as exc:
            raise exc.last_attempt.exception from exc

    async def run_model(
        self,
        prompt: str,
        model: str = "llama2:7b",
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        payload: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if options:
            payload["options"] = options

        response = await self._request("POST", "/api/generate", json=payload)
        body = response.json()
        return body.get("response", "")

    async def pull_model(self, model: str) -> None:
        payload = {"name": model}
        await self._request("POST", "/api/pull", json=payload)

    async def list_models(self) -> List[Dict[str, Any]]:
        response = await self._request("GET", "/api/tags")
        body = response.json()
        return body.get("models", [])

    async def check_connection(self) -> bool:
        try:
            await self._request("GET", "/api/tags")
            return True
        except Exception as exc:  # pragma: no cover - simple network probe
            logger.warning("ollama_connection_failed", error=str(exc))
            return False