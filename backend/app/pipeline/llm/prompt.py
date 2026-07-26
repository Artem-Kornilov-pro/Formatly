from app.pipeline.schemas import ParagraphRole, ParsedParagraph

ALLOWED_ROLES = [role.value for role in ParagraphRole]

SYSTEM_PROMPT = (
    "You classify paragraphs from a Word document by semantic role. "
    "The current Word style name is a hint, not the answer - judge from the "
    "text itself. Respond with exactly one role per paragraph given, using "
    "the same index values you were given.\n\n"
    "You may also make two narrow, additive edits. Both are optional - leave "
    "them out whenever you're not confident:\n"
    "1. completion: if a paragraph's text is obviously cut off mid-sentence "
    "(trails off with no closing punctuation, clearly missing its ending), "
    "give a short completion - a few words or a short clause that finishes "
    "that exact sentence. It will be appended after the existing text, "
    "never replacing it. Do not complete paragraphs that are merely short; "
    "only ones that are genuinely truncated.\n"
    "2. generated_title: if none of the paragraphs are classified as "
    "'title' and you can confidently infer a short, appropriate title for "
    "the whole document from its content, provide one.\n\n"
    "Hard rules, no exceptions: never rewrite, shorten, paraphrase, or "
    "delete any existing text. Never invent whole new paragraphs or "
    "sections. A completion is only ever appended to the one paragraph it "
    "belongs to."
)


def build_paragraph_listing(paragraphs: list[ParsedParagraph]) -> str:
    return "\n".join(f"{p.index}. [{p.style_name}] {p.text}" for p in paragraphs)
