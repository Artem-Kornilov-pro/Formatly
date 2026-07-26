import enum

from pydantic import BaseModel

# Shared between formatter.py (which writes this heading) and validator.py
# (which needs to recognize and skip it, since it's synthetic content the
# formatter adds rather than part of the original document).
TOC_HEADING_TEXT = "СОДЕРЖАНИЕ"


class ParagraphRole(enum.StrEnum):
    TITLE = "title"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BODY = "body"
    LIST_ITEM = "list_item"
    FIGURE_CAPTION = "figure_caption"
    TABLE_CAPTION = "table_caption"
    APPENDIX_START = "appendix_start"


class ParsedParagraph(BaseModel):
    index: int
    text: str
    style_name: str


class ClassifiedParagraph(BaseModel):
    index: int
    text: str
    role: ParagraphRole
    # Short text to append after this paragraph's existing text when it's
    # obviously cut off mid-sentence - additive only, never a replacement.
    completion: str | None = None


class ClassificationResult(BaseModel):
    paragraphs: list[ClassifiedParagraph]
    # A short document title, only present when none of `paragraphs` was
    # classified as `title` and the classifier could confidently infer one.
    generated_title: str | None = None


def should_insert_generated_title(
    classified: list[ClassifiedParagraph], generated_title: str | None
) -> bool:
    """Whether apply_formatting/validate_document should treat a generated
    title as a real, synthetic first paragraph.

    Both formatter and validator derive this independently from the same
    inputs rather than one telling the other, so they can't drift out of
    sync about whether a title paragraph was actually inserted.
    """
    if not generated_title:
        return False
    return not any(paragraph.role == ParagraphRole.TITLE for paragraph in classified)
