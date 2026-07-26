from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from app.pipeline.rules import FormattingRules
from app.pipeline.schemas import (
    TOC_HEADING_TEXT,
    ClassifiedParagraph,
    ParagraphRole,
    should_insert_generated_title,
)

_ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

# Word stores lengths like margins/indents in twips (1/20 pt), not the EMU a
# Length is constructed from, so round-tripping through a saved .docx always
# introduces a fraction-of-a-mm of noise. Comparing rounded integers instead
# of this tolerance is what let a default of exactly 12.5mm land on Python's
# round-half-to-even boundary and produce a false positive (12 vs 13).
_MM_TOLERANCE = 0.5


def _mm_mismatch(actual: float, expected: float) -> bool:
    return abs(actual - expected) > _MM_TOLERANCE


def _is_toc_field_paragraph(paragraph) -> bool:
    return any(
        instr.text and "TOC" in instr.text for instr in paragraph._p.iter(qn("w:instrText"))
    )


def _synthetic_toc_paragraph_ids(paragraphs: list) -> set[int]:
    """id()s of the "СОДЕРЖАНИЕ" heading + TOC field paragraphs the formatter
    adds, so validation can skip them and keep `classified`'s indices aligned
    with the rest of the (unshifted) original paragraphs.

    A paragraph is only treated as the synthetic heading when it immediately
    precedes a recognized TOC field paragraph - matching exactly how the
    formatter inserts the pair - so a user's own paragraph that happens to
    read "СОДЕРЖАНИЕ" isn't misidentified.
    """
    synthetic: set[int] = set()
    for i, paragraph in enumerate(paragraphs):
        if not _is_toc_field_paragraph(paragraph):
            continue
        synthetic.add(id(paragraph._p))
        if i > 0 and paragraphs[i - 1].text == TOC_HEADING_TEXT:
            synthetic.add(id(paragraphs[i - 1]._p))
    return synthetic


def validate_document(
    output_path: Path,
    classified: list[ClassifiedParagraph],
    rules: FormattingRules,
    generated_title: str | None = None,
) -> list[str]:
    document = Document(str(output_path))
    issues: list[str] = []

    section = document.sections[0]
    actual_margins_mm = {
        "top": section.top_margin.mm,
        "bottom": section.bottom_margin.mm,
        "left": section.left_margin.mm,
        "right": section.right_margin.mm,
    }
    for side, expected in rules.margins_mm.model_dump().items():
        actual = actual_margins_mm[side]
        if _mm_mismatch(actual, expected):
            issues.append(f"{side} margin is {round(actual)}mm, expected {round(expected)}mm")

    expected_alignment = _ALIGNMENTS[rules.paragraph_alignment]
    role_by_index = {paragraph.index: paragraph.role for paragraph in classified}

    paragraphs = document.paragraphs
    synthetic_ids = _synthetic_toc_paragraph_ids(paragraphs)
    title_was_generated = rules.ai_light_editing_enabled and should_insert_generated_title(
        classified, generated_title
    )

    original_index = 0
    for i, paragraph in enumerate(paragraphs):
        if title_was_generated and i == 0:
            continue
        if id(paragraph._p) in synthetic_ids:
            continue
        index = original_index
        original_index += 1

        role = role_by_index.get(index, ParagraphRole.BODY)
        if role != ParagraphRole.BODY:
            continue

        if paragraph.paragraph_format.alignment != expected_alignment:
            issues.append(
                f"paragraph {index}: alignment is {paragraph.paragraph_format.alignment!r}, "
                f"expected {rules.paragraph_alignment!r}"
            )

        if rules.paragraph_indent_enabled:
            indent = paragraph.paragraph_format.first_line_indent
            actual_indent_mm = indent.mm if indent is not None else 0
            if _mm_mismatch(actual_indent_mm, rules.paragraph_indent_mm):
                issues.append(
                    f"paragraph {index}: first-line indent is {round(actual_indent_mm)}mm, "
                    f"expected {round(rules.paragraph_indent_mm)}mm"
                )

        for run in paragraph.runs:
            if run.font.name != rules.font_family:
                issues.append(
                    f"paragraph {index}: font is {run.font.name!r}, "
                    f"expected {rules.font_family!r}"
                )
            if run.font.size is not None and round(run.font.size.pt) != rules.font_size_pt:
                issues.append(
                    f"paragraph {index}: size is {run.font.size.pt}pt, "
                    f"expected {rules.font_size_pt}pt"
                )

    return issues
