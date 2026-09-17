"""Replaceable Chat, Embedding and Reranker providers."""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from typing import Any, Protocol

import httpx

from app.config import get_settings


class ProviderUnavailable(RuntimeError):
    """The configured provider cannot serve a request."""


class ProviderNotConfigured(ProviderUnavailable):
    """The provider is missing required endpoint or credentials.

    Distinguishes "nothing to run yet" from a transient failure, so callers
    can mark the derived job as skipped instead of failed.
    """


class ProviderRequestError(RuntimeError):
    """The provider rejected a request after bounded retries."""


@dataclass(frozen=True)
class ChatResult:
    content: str
    model: str
    token_usage: int | None = None


class ChatProvider(Protocol):
    name: str
    model: str

    def complete(
        self,
        messages: Sequence[dict[str, str]],
        *,
        max_tokens: int = 800,
        temperature: float = 0.0,
        top_p: float = 1.0,
        json_mode: bool = False,
    ) -> ChatResult: ...


class EmbeddingProvider(Protocol):
    name: str
    model: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class RerankerProvider(Protocol):
    name: str

    def rerank(self, query: str, documents: Sequence[str]) -> list[float]: ...


class OCRProvider(Protocol):
    name: str
    model: str

    def extract(self, image_bytes: bytes, *, language: str, timeout_seconds: int) -> str: ...


class ImageDescriptionProvider(Protocol):
    name: str
    model: str

    def describe(self, image_bytes: bytes, *, media_type: str) -> str: ...


class TesseractOCRProvider:
    name = "tesseract"
    model = "tesseract-local"

    def extract(self, image_bytes: bytes, *, language: str, timeout_seconds: int) -> str:
        try:
            import pytesseract
            from PIL import Image

            with Image.open(BytesIO(image_bytes)) as image:
                return pytesseract.image_to_string(
                    image, lang=language, timeout=max(1, timeout_seconds)
                ).strip()
        except ProviderUnavailable:
            raise
        except Exception as exc:
            error_name = type(exc).__name__
            raise ProviderUnavailable(f"Local OCR failed: {error_name}") from exc


class OpenAICompatibleImageDescriptionProvider:
    """Optional vision provider; disabled unless a base URL and model are configured."""

    name = "openai-compatible-vision"

    def __init__(self, base_url: str, model: str, api_key: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def describe(self, image_bytes: bytes, *, media_type: str) -> str:
        if not self.base_url or not self.model or not self.api_key:
            raise ProviderUnavailable("Image description provider is not configured")
        import base64

        encoded = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Describe this image factually for a personal knowledge base. "
                                "Return one short paragraph, no speculation."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{encoded}"},
                        },
                    ],
                }
            ],
            "temperature": 0.0,
            "max_tokens": 400,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = str(data["choices"][0]["message"].get("content", "")).strip()
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise ProviderUnavailable("Image description request failed") from exc
        if not content:
            raise ProviderUnavailable("Image description provider returned an empty result")
        return content[:4_000]


class FastEmbedProvider:
    name = "fastembed"

    def __init__(self, model: str, dimensions: int):
        self.model = model
        self.dimensions = dimensions
        self._model: Any | None = None

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model, lazy_load=True)
        except Exception as exc:
            raise ProviderUnavailable(f"FastEmbed model unavailable: {self.model}") from exc
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            vectors = [list(map(float, vector)) for vector in self._load().embed(list(texts))]
        except ProviderUnavailable:
            raise
        except Exception as exc:
            raise ProviderUnavailable(f"FastEmbed model failed: {self.model}") from exc
        if len(vectors) != len(texts):
            raise ProviderUnavailable("Embedding provider returned an unexpected result count")
        if any(len(vector) != self.dimensions for vector in vectors):
            actual = {len(vector) for vector in vectors}
            raise ProviderUnavailable(
                f"Embedding dimension mismatch: expected {self.dimensions}, got {sorted(actual)}"
            )
        return vectors


class OpenAICompatibleChatProvider:
    name = "openai-compatible"

    def __init__(self, base_url: str, model: str, api_key: str, timeout: int, max_retries: int):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max(0, max_retries)

    def complete(
        self,
        messages: Sequence[dict[str, str]],
        *,
        max_tokens: int = 800,
        temperature: float = 0.0,
        top_p: float = 1.0,
        json_mode: bool = False,
    ) -> ChatResult:
        if not self.base_url or not self.model:
            raise ProviderNotConfigured("Chat provider is not configured")
        if not self.api_key:
            raise ProviderNotConfigured("Chat provider credentials are not configured")
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": list(messages),
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": get_settings().chat_enable_thinking},
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                message = data["choices"][0]["message"]
                usage = data.get("usage") or {}
                return ChatResult(
                    content=str(message.get("content", "")),
                    model=str(data.get("model", self.model)),
                    token_usage=usage.get("total_tokens"),
                )
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(min(2**attempt, 4))
        raise ProviderRequestError(
            f"Chat provider request failed after {self.max_retries + 1} attempts"
        ) from last_error


class MockEmbeddingProvider:
    name = "mock"
    model = "mock"

    def __init__(self, dimensions: int = 8):
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for index, char in enumerate(text):
                vector[index % self.dimensions] += ord(char) / 1000
            norm = sum(item * item for item in vector) ** 0.5 or 1.0
            vectors.append([item / norm for item in vector])
        return vectors


class MockChatProvider:
    name = "mock"
    model = "mock"

    def __init__(self, content: str = "{}"):
        self.content = content

    def complete(
        self,
        messages: Sequence[dict[str, str]],
        *,
        max_tokens: int = 800,
        temperature: float = 0.0,
        top_p: float = 1.0,
        json_mode: bool = False,
    ) -> ChatResult:
        return ChatResult(content=self.content, model=self.model)


class MockRerankerProvider:
    name = "mock"

    def rerank(self, query: str, documents: Sequence[str]) -> list[float]:
        query_terms = set(query.lower().split())
        return [sum(term in document.lower() for term in query_terms) for document in documents]


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider | None:
    settings = get_settings()
    if settings.embedding_provider.lower() in {"", "none", "disabled"}:
        return None
    if settings.embedding_provider.lower() == "fastembed":
        return FastEmbedProvider(settings.embedding_model, settings.embedding_dimensions)
    raise ProviderUnavailable(f"Unsupported embedding provider: {settings.embedding_provider}")


TASK_USER_PROMPT = "请严格按上述指令输出结果。"


def task_messages(
    instruction: str, *, user_prompt: str = TASK_USER_PROMPT
) -> list[dict[str, str]]:
    """构造符合 OpenAI Chat 协议的消息序列。

    部分 OpenAI 兼容服务（如 llama.cpp 加载 Qwen3 系 GGUF 时的官方 Jinja 模板）
    要求 messages 中必须存在 user 消息，否则直接返回 500
    （`Jinja Exception: No user query found in messages.`）。
    业务指令仍放在 system 中，这里补一条 user 消息作为触发。
    """
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_prompt},
    ]


def get_chat_provider(
    *, model_override: str | None = None, provider_override: str | None = None
) -> ChatProvider:
    settings = get_settings()
    provider_name = (provider_override or "openai-compatible").casefold()
    if provider_name not in {"openai-compatible", "openai_compatible"}:
        raise ProviderUnavailable(f"Unsupported chat provider: {provider_override}")
    return OpenAICompatibleChatProvider(
        settings.chat_base_url,
        model_override or settings.chat_model,
        settings.chat_api_key,
        settings.chat_timeout_seconds,
        settings.chat_max_retries,
    )


@lru_cache(maxsize=1)
def get_ocr_provider() -> OCRProvider | None:
    settings = get_settings()
    if not settings.ocr_enabled:
        return None
    return TesseractOCRProvider()


def get_image_description_provider() -> ImageDescriptionProvider | None:
    settings = get_settings()
    if not settings.image_description_enabled:
        return None
    if not settings.image_description_base_url or not settings.image_description_model:
        return None
    return OpenAICompatibleImageDescriptionProvider(
        settings.image_description_base_url,
        settings.image_description_model,
        settings.chat_api_key,
        settings.image_description_timeout_seconds,
    )


def parse_json_content(content: str) -> dict[str, Any]:
    """Small shared helper for providers; strict validation happens at call sites."""
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError("Provider JSON must be an object")
    return value
