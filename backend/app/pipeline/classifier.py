from anthropic import Anthropic

from app.core.config import get_settings
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
                        "role": {"type": "string", "enum": [role.value for role in ParagraphRole]},
                    },
                    "required": ["index", "role"],
                },
            }
        },
        "required": ["paragraphs"],
    },
}

_SYSTEM_PROMPT = (
    "You classify paragraphs from a Word document by semantic role. "
    "The current Word style name is a hint, not the answer - judge from the "
    "text itself. Call the classify_paragraphs tool exactly once, with one "
    "entry per paragraph given, using the same index values you were given."
)


def classify_paragraphs(
    paragraphs: list[ParsedParagraph], client: Anthropic
) -> list[ClassifiedParagraph]:
    if not paragraphs:
        return []

    settings = get_settings()
    listing = "\n".join(f"{p.index}. [{p.style_name}] {p.text}" for p in paragraphs)

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "classify_paragraphs"},
        messages=[{"role": "user", "content": listing}],
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
