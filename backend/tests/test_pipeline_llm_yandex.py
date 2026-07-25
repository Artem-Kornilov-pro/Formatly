import json
from types import SimpleNamespace

import pytest

from app.pipeline.llm.yandex_provider import YandexClassifier
from app.pipeline.schemas import ParagraphRole, ParsedParagraph


class FakeResponses:
    def __init__(self, output_text: str):
        self._output_text = output_text
        self.last_call: dict | None = None

    def create(self, **kwargs):
        self.last_call = kwargs
        return SimpleNamespace(output_text=self._output_text)


class FakeYandexClient:
    def __init__(self, output_text: str):
        self.responses = FakeResponses(output_text)


MODEL_URI = "gpt://b1gkn6ulsqd1m6d7t3hv/deepseek-v4-flash/latest"


def test_classify_maps_roles_by_index():
    paragraphs = [
        ParsedParagraph(index=0, text="Introduction", style_name="Heading 1"),
        ParsedParagraph(index=2, text="Body text.", style_name="Normal"),
    ]
    payload = json.dumps(
        {"paragraphs": [{"index": 0, "role": "heading_1"}, {"index": 2, "role": "body"}]}
    )
    client = FakeYandexClient(payload)
    classifier = YandexClassifier(client, model_uri=MODEL_URI)

    result = classifier.classify(paragraphs)

    assert result[0].role == ParagraphRole.HEADING_1
    assert result[0].text == "Introduction"
    assert result[1].role == ParagraphRole.BODY


def test_classify_tolerates_markdown_fences_around_json():
    paragraphs = [ParsedParagraph(index=0, text="Hello", style_name="Normal")]
    fenced = '```json\n{"paragraphs": [{"index": 0, "role": "body"}]}\n```'
    client = FakeYandexClient(fenced)
    classifier = YandexClassifier(client, model_uri=MODEL_URI)

    result = classifier.classify(paragraphs)

    assert result[0].role == ParagraphRole.BODY


def test_classify_defaults_missing_index_to_body():
    paragraphs = [ParsedParagraph(index=5, text="Orphan paragraph", style_name="Normal")]
    client = FakeYandexClient(json.dumps({"paragraphs": []}))
    classifier = YandexClassifier(client, model_uri=MODEL_URI)

    result = classifier.classify(paragraphs)

    assert result[0].role == ParagraphRole.BODY


def test_classify_returns_empty_list_without_calling_the_client():
    client = FakeYandexClient(json.dumps({"paragraphs": []}))
    classifier = YandexClassifier(client, model_uri=MODEL_URI)

    result = classifier.classify([])

    assert result == []
    assert client.responses.last_call is None


def test_classify_sends_model_uri_and_paragraph_listing():
    paragraphs = [ParsedParagraph(index=0, text="Hello", style_name="Normal")]
    client = FakeYandexClient(json.dumps({"paragraphs": [{"index": 0, "role": "body"}]}))
    classifier = YandexClassifier(client, model_uri=MODEL_URI)

    classifier.classify(paragraphs)

    call = client.responses.last_call
    assert call["model"] == MODEL_URI
    assert "0. [Normal] Hello" in call["input"]


def test_classify_raises_on_unparseable_response():
    client = FakeYandexClient("sorry, I can't help with that")
    classifier = YandexClassifier(client, model_uri=MODEL_URI)

    with pytest.raises(json.JSONDecodeError):
        classifier.classify([ParsedParagraph(index=0, text="Hello", style_name="Normal")])
