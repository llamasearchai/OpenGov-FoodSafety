"""AI agent service for OpenGov Food."""

from __future__ import annotations

import json
from typing import Any, Dict

import httpx
import structlog
from openai import AsyncOpenAI

from ..core.config import get_settings

logger = structlog.get_logger(__name__)


class AgentService:
    """Service for managing AI-driven inspection analysis."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.openai_client: AsyncOpenAI | None = None
        if self.settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def run_analysis(
        self,
        prompt: str,
        model: str = "gpt-4",
        provider: str = "openai",
    ) -> Dict[str, Any]:
        """Run an inspection analysis and return structured findings."""
        if provider == "openai" and self.openai_client:
            return await self._run_openai_analysis(prompt=prompt, model=model)
        if provider == "ollama":
            return await self._run_ollama_analysis(prompt=prompt, model=model)
        return await self._run_mock_analysis(prompt)

    async def _run_openai_analysis(self, prompt: str, model: str) -> Dict[str, Any]:
        if not self.openai_client:
            raise ValueError("OpenAI client not initialised")

        system_prompt = (
            "You are a senior food safety inspector."
            " Generate inspection findings with sections for violations,"
            " corrective actions, compliance score, and public health narrative."
        )

        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1200,
            )
        except Exception as exc:  # pragma: no cover - API call
            logger.error("openai_analysis_failed", error=str(exc))
            return await self._run_mock_analysis(prompt)

        message = response.choices[0].message.content
        try:
            data = json.loads(message) if message else {}
        except json.JSONDecodeError:
            data = {"analysis": message}
        data.setdefault("provider", "openai")
        data.setdefault("model", model)
        return data

    async def _run_ollama_analysis(self, prompt: str, model: str) -> Dict[str, Any]:
        base_url = self.settings.ollama_base_url
        if not base_url:
            raise ValueError("Ollama base URL is not configured")

        payload = {"model": model, "prompt": prompt, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(f"{base_url}/api/generate", json=payload)
                response.raise_for_status()
                body = response.json()
                raw_response = body.get("response", "")
                try:
                    data = json.loads(raw_response)
                except json.JSONDecodeError:
                    data = {"analysis": raw_response}
                data.update({"provider": "ollama", "model": model})
                return data
        except Exception as exc:  # pragma: no cover - API call
            logger.error("ollama_analysis_failed", error=str(exc))
            return await self._run_mock_analysis(prompt)

    async def _run_mock_analysis(self, prompt: str) -> Dict[str, Any]:
        return {
            "analysis": "Facility inspection summary with focus on critical food safety checkpoints",
            "violations": ["No critical violations detected"],
            "corrective_actions": ["Continue temperature monitoring protocols"],
            "compliance_score": 0.85,
            "provider": "mock",
            "model": "mock-analysis",
            "prompt": prompt,
        }

    async def chat(self, message: str) -> str:
        if not self.openai_client:
            return "AI chat is unavailable. Configure an OpenAI API key to enable this feature."

        system_prompt = (
            "You are an assistant that helps inspectors summarise field notes"
            " and recommend next steps. Provide concise, actionable guidance."
        )

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                temperature=0.5,
                max_tokens=600,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # pragma: no cover - API call
            logger.error("openai_chat_failed", error=str(exc))
            return "Unable to complete chat request."