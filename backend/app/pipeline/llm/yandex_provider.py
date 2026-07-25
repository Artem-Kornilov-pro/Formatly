import json
import re

import openai

from app.pipeline.llm.prompt import ALLOWED_ROLES, SYSTEM_PROMPT, build_paragraph_listing
from app.pipeline.schemas import ClassifiedParagraph, ParagraphRole, ParsedParagraph

# Yandex Cloud's OpenAI-compatible `responses` endpoint doesn't offer
# tool-use/structured output the way Anthropic does, so the schema has to be
# enforced by instruction + tolerant parsing instead of a constrained schema.
_INSTRUCTIONS = (
    f"{SYSTEM_PROMPT} Respond with nothing but a single JSON object of the exact "
    'shape {"paragraphs": [{"index": <int>, "role": "<role>"}, ...]}, where '
    f"<role> is one of: {', '.join(ALLOWED_ROLES)}. No markdown fences, no "
    "commentary, no other text before or after the JSON."
)

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> dict:
    match = _JSON_OBJECT_RE.search(text)
    payload = match.group(0) if match else text
    return json.loads(payload)


class YandexClassifier:
    def __init__(self, client: openai.OpenAI, model_uri: str):
        self._client = client
        self._model_uri = model_uri

    def classify(self, paragraphs: list[ParsedParagraph]) -> list[ClassifiedParagraph]:
        if not paragraphs:
            return []

        response = self._client.responses.create(
            model=self._model_uri,
            temperature=0.0,
            instructions=_INSTRUCTIONS,
            input=build_paragraph_listing(paragraphs),
            max_output_tokens=4096,
        )

        payload = _extract_json(response.output_text)
        roles_by_index = {
            entry["index"]: ParagraphRole(entry["role"]) for entry in payload["paragraphs"]
        }

        return [
            ClassifiedParagraph(
                index=paragraph.index,
                text=paragraph.text,
                role=roles_by_index.get(paragraph.index, ParagraphRole.BODY),
            )
            for paragraph in paragraphs
        ]
