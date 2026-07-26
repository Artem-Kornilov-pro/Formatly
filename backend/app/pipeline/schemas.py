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
