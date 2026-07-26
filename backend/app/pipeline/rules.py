from typing import Literal

from pydantic import BaseModel, Field

Alignment = Literal["left", "center", "right", "justify"]


class MarginsMm(BaseModel):
    top: float = 20
    bottom: float = 20
    left: float = 30
    right: float = 15


class FormattingRules(BaseModel):
    """Single source of truth for what the formatter/validator can apply.

    A FormattingProfile.rules JSONB blob is validated against this model, so
    any field the stored JSON doesn't specify falls back to the default here
    - existing profiles keep working untouched, and a profile can override
    any subset of fields without needing to restate the rest.
    """

    font_family: str = "Times New Roman"
    font_size_pt: int = 14
    line_spacing: float = 1.5
    margins_mm: MarginsMm = Field(default_factory=MarginsMm)

    bold_headings: bool = True
    italic_headings: bool = False
    center_headings: bool = True
    heading_size_bump_pt: int = 2
    page_break_before_heading_1: bool = False

    paragraph_alignment: Alignment = "justify"
    paragraph_indent_enabled: bool = True
    paragraph_indent_mm: float = 12.5
