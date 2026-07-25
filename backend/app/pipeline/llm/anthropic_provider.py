from anthropic import Anthropic

from app.pipeline.llm.prompt import ALLOWED_ROLES, SYSTEM_PROMPT, build_paragraph_listing
from app.pipeline.schemas import ClassifiedParagraph, ParagraphRole, ParsedParagraph

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
                    },
                    "required": ["index", "role"],
                },
            }
        },
        "required": ["paragraphs"],
    },
}


class AnthropicClassifier:
    def __init__(self, client: Anthropic, model: str):
        self._client = client
        self._model = model

    def classify(self, paragraphs: list[ParsedParagraph]) -> list[ClassifiedParagraph]:
        if not paragraphs:
            return []

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "classify_paragraphs"},
            messages=[{"role": "user", "content": build_paragraph_listing(paragraphs)}],
        )

        tool_use = next(block for block in response.content if block.type == "tool_use")
        roles_by_index = {
            entry["index"]: ParagraphRole(entry["role"]) for entry in tool_use.input["paragraphs"]
        }

        return [
            ClassifiedParagraph(
                index=paragraph.index,
                text=paragraph.text,
                role=roles_by_index.get(paragraph.index, ParagraphRole.BODY),
            )
            for paragraph in paragraphs
        ]
