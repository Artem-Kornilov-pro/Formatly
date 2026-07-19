from types import SimpleNamespace

from app.pipeline.classifier import classify_paragraphs
from app.pipeline.schemas import ParagraphRole, ParsedParagraph


class FakeMessages:
    def __init__(self, tool_input: dict):
        self._tool_input = tool_input
        self.last_call: dict | None = None

    def create(self, **kwargs):
        self.last_call = kwargs
        block = SimpleNamespace(type="tool_use", input=self._tool_input)
        return SimpleNamespace(content=[block])


class FakeAnthropicClient:
    def __init__(self, tool_input: dict):
        self.messages = FakeMessages(tool_input)


def test_classify_paragraphs_maps_roles_by_index():
    paragraphs = [
        ParsedParagraph(index=0, text="Introduction", style_name="Heading 1"),
        ParsedParagraph(index=2, text="Body text.", style_name="Normal"),
    ]
    client = FakeAnthropicClient(
        {"paragraphs": [{"index": 0, "role": "heading_1"}, {"index": 2, "role": "body"}]}
    )

    result = classify_paragraphs(paragraphs, client)

    assert result[0].role == ParagraphRole.HEADING_1
    assert result[0].text == "Introduction"
    assert result[1].role == ParagraphRole.BODY


def test_classify_paragraphs_defaults_missing_index_to_body():
    paragraphs = [ParsedParagraph(index=5, text="Orphan paragraph", style_name="Normal")]
    client = FakeAnthropicClient({"paragraphs": []})  # model omitted this index

    result = classify_paragraphs(paragraphs, client)

    assert result[0].role == ParagraphRole.BODY


def test_classify_paragraphs_returns_empty_list_without_calling_the_client():
    client = FakeAnthropicClient({"paragraphs": []})

    result = classify_paragraphs([], client)

    assert result == []
    assert client.messages.last_call is None


def test_classify_paragraphs_sends_tool_choice_and_paragraph_listing():
    paragraphs = [ParsedParagraph(index=0, text="Hello", style_name="Normal")]
    client = FakeAnthropicClient({"paragraphs": [{"index": 0, "role": "body"}]})

    classify_paragraphs(paragraphs, client)

    call = client.messages.last_call
    assert call["tool_choice"] == {"type": "tool", "name": "classify_paragraphs"}
    assert "0. [Normal] Hello" in call["messages"][0]["content"]
