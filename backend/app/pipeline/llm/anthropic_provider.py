from anthropic import Anthropic

from app.pipeline.llm.prompt import ALLOWED_ROLES, SYSTEM_PROMPT, build_paragraph_listing
from app.pipeline.schemas import (
    ClassificationResult,
    ClassifiedParagraph,
    ParagraphRole,
    ParsedParagraph,
)

_TOOL = {
    "name": "classify_paragraphs",
    "description": "Assign a semantic role to each paragraph of a document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "paragraphs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "role": {"type": "string", "enum": ALLOWED_ROLES},
                        "completion": {
                            "type": "string",
                            "description": (
                                "Short text to append when this paragraph is obviously "
                                "cut off mid-sentence. Omit entirely otherwise."
                            ),
                        },
                    },
                    "required": ["index", "role"],
                },
            },
            "generated_title": {
                "type": "string",
                "description": (
                    "A short document title, only if none of the paragraphs were "
                    "classified as 'title' and one can be confidently inferred. Omit "
                    "entirely otherwise."
                ),
            },
        },
        "required": ["paragraphs"],
    },
}


class AnthropicClassifier:
    def __init__(self, client: Anthropic, model: str):
        self._client = client
        self._model = model

    def classify(self, paragraphs: list[ParsedParagraph]) -> ClassificationResult:
        if not paragraphs:
            return ClassificationResult(paragraphs=[])

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "classify_paragraphs"},
            messages=[{"role": "user", "content": build_paragraph_listing(paragraphs)}],
        )

        tool_use = next(block for block in response.content if block.type == "tool_use")
        entries_by_index = {entry["index"]: entry for entry in tool_use.input["paragraphs"]}

        classified = [
            ClassifiedParagraph(
                index=paragraph.index,
                text=paragraph.text,
                role=ParagraphRole(entries_by_index[paragraph.index]["role"])
                if paragraph.index in entries_by_index
                else ParagraphRole.BODY,
                completion=entries_by_index.get(paragraph.index, {}).get("completion") or None,
            )
            for paragraph in paragraphs
        ]
        return ClassificationResult(
            paragraphs=classified,
            generated_title=tool_use.input.get("generated_title") or None,
        )
