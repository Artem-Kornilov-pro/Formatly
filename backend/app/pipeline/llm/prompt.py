from app.pipeline.schemas import ParagraphRole, ParsedParagraph

ALLOWED_ROLES = [role.value for role in ParagraphRole]

SYSTEM_PROMPT = (
    "You classify paragraphs from a Word document by semantic role. "
    "The current Word style name is a hint, not the answer - judge from the "
    "text itself. Respond with exactly one role per paragraph given, using "
    "the same index values you were given."
)


def build_paragraph_listing(paragraphs: list[ParsedParagraph]) -> str:
    return "\n".join(f"{p.index}. [{p.style_name}] {p.text}" for p in paragraphs)
