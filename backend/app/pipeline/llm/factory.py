from anthropic import Anthropic
from openai import OpenAI

from app.core.config import Settings, get_settings
from app.pipeline.llm.anthropic_provider import AnthropicClassifier
from app.pipeline.llm.base import ParagraphClassifier
from app.pipeline.llm.yandex_provider import YandexClassifier

YANDEX_BASE_URL = "https://ai.api.cloud.yandex.net/v1"


def build_classifier(settings: Settings | None = None) -> ParagraphClassifier:
    settings = settings or get_settings()

    if settings.llm_provider == "yandex":
        client = OpenAI(
            api_key=settings.yandex_api_key,
            base_url=YANDEX_BASE_URL,
            project=settings.yandex_folder_id,
        )
        model_uri = f"gpt://{settings.yandex_folder_id}/{settings.yandex_model}"
        return YandexClassifier(client, model_uri)

    if settings.llm_provider == "anthropic":
        client = Anthropic(api_key=settings.anthropic_api_key)
        return AnthropicClassifier(client, settings.anthropic_model)

    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
