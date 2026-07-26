from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

from app.pipeline.rules import FormattingRules
from app.pipeline.schemas import ClassifiedParagraph, ParagraphRole

_HEADING_ROLES = {ParagraphRole.HEADING_1, ParagraphRole.HEADING_2, ParagraphRole.HEADING_3}
# heading_size_bump_pt scaled by level: heading 1 gets the full bump, heading
# 2 gets half, heading 3 gets none.
_HEADING_BUMP_SCALE = {
    ParagraphRole.HEADING_1: 1.0,
    ParagraphRole.HEADING_2: 0.5,
    ParagraphRole.HEADING_3: 0.0,
}
_ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _set_run_font(run, font_family: str) -> None:
    run.font.name = font_family
    # python-docx's font.name setter only writes w:ascii - Cyrillic and other
    # non-Latin runs are rendered via w:hAnsi/w:eastAsia/w:cs, so without this
    # the font change silently doesn't apply to Russian text.
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:eastAsia", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), font_family)


def apply_formatting(
    input_path: Path,
    output_path: Path,
    classified: list[ClassifiedParagraph],
    rules: FormattingRules,
) -> list[str]:
    document = Document(str(input_path))

    for section in document.sections:
        section.top_margin = Mm(rules.margins_mm.top)
        section.bottom_margin = Mm(rules.margins_mm.bottom)
        section.left_margin = Mm(rules.margins_mm.left)
        section.right_margin = Mm(rules.margins_mm.right)

    role_by_index = {paragraph.index: paragraph.role for paragraph in classified}
    body_alignment = _ALIGNMENTS[rules.paragraph_alignment]

    for index, paragraph in enumerate(document.paragraphs):
        role = role_by_index.get(index, ParagraphRole.BODY)
        is_heading = role in _HEADING_ROLES

        size_pt = rules.font_size_pt
        if is_heading:
            size_pt += round(rules.heading_size_bump_pt * _HEADING_BUMP_SCALE[role])

        paragraph.paragraph_format.line_spacing = rules.line_spacing

        if is_heading:
            paragraph.paragraph_format.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if rules.center_headings else WD_ALIGN_PARAGRAPH.LEFT
            )
            paragraph.paragraph_format.first_line_indent = Mm(0)
            if role == ParagraphRole.HEADING_1:
                paragraph.paragraph_format.page_break_before = rules.page_break_before_heading_1
        else:
            paragraph.paragraph_format.alignment = body_alignment
            paragraph.paragraph_format.first_line_indent = (
                Mm(rules.paragraph_indent_mm) if rules.paragraph_indent_enabled else Mm(0)
            )

        for run in paragraph.runs:
            _set_run_font(run, rules.font_family)
            run.font.size = Pt(size_pt)
            run.font.bold = is_heading and rules.bold_headings
            run.font.italic = is_heading and rules.italic_headings

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(output_path))

    return _describe_changes(rules)


def _describe_changes(rules: FormattingRules) -> list[str]:
    changes = [
        f"set page margins to {rules.margins_mm.top}/{rules.margins_mm.bottom}/"
        f"{rules.margins_mm.left}/{rules.margins_mm.right}mm (top/bottom/left/right)",
        f"applied {rules.font_family} {rules.font_size_pt}pt, line spacing {rules.line_spacing}, "
        f"{rules.paragraph_alignment} alignment to body text",
    ]

    if rules.paragraph_indent_enabled:
        changes.append(
            f"applied a {rules.paragraph_indent_mm}mm first-line indent to body paragraphs"
        )

    heading_style = []
    if rules.bold_headings:
        heading_style.append("bold")
    if rules.italic_headings:
        heading_style.append("italic")
    if rules.center_headings:
        heading_style.append("centered")
    if heading_style:
        changes.append(
            f"styled headings as {', '.join(heading_style)}, "
            f"enlarged by up to {rules.heading_size_bump_pt}pt"
        )

    if rules.page_break_before_heading_1:
        changes.append("inserted a page break before each top-level heading")

    return changes
