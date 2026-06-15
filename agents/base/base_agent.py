from abc import ABC, abstractmethod

import httpx
from langchain_anthropic import ChatAnthropic

from agent.config import settings


class BaseAssessmentAgent(ABC):

    def __init__(self):
        self.llm = ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            max_tokens=4096,
        )
        self._api = settings.api_base_url

    async def api_get(self, path: str) -> dict:
        async with httpx.AsyncClient(base_url=self._api, timeout=30) as client:
            resp = await client.get(path)
            resp.raise_for_status()
            return resp.json()

    async def api_post(self, path: str, body: dict) -> dict:
        async with httpx.AsyncClient(base_url=self._api, timeout=30) as client:
            resp = await client.post(path, json=body)
            resp.raise_for_status()
            return resp.json()

    async def api_patch(self, path: str, body: dict) -> dict:
        async with httpx.AsyncClient(base_url=self._api, timeout=30) as client:
            resp = await client.patch(path, json=body)
            resp.raise_for_status()
            return resp.json()

    @abstractmethod
    def build_graph(self):
        pass
