from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

from app.pipeline.schemas import ClassifiedParagraph, ParagraphRole

_HEADING_ROLES = {ParagraphRole.HEADING_1, ParagraphRole.HEADING_2, ParagraphRole.HEADING_3}
_HEADING_SIZE_BUMP_PT = {
    ParagraphRole.HEADING_1: 2,
    ParagraphRole.HEADING_2: 1,
    ParagraphRole.HEADING_3: 0,
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
    rules: dict,
) -> list[str]:
    document = Document(str(input_path))

    font_family = rules["font_family"]
    font_size_pt = rules["font_size_pt"]
    line_spacing = rules["line_spacing"]
    margins_mm = rules["margins_mm"]

    for section in document.sections:
        section.top_margin = Mm(margins_mm["top"])
        section.bottom_margin = Mm(margins_mm["bottom"])
        section.left_margin = Mm(margins_mm["left"])
        section.right_margin = Mm(margins_mm["right"])

    role_by_index = {paragraph.index: paragraph.role for paragraph in classified}

    for index, paragraph in enumerate(document.paragraphs):
        role = role_by_index.get(index, ParagraphRole.BODY)
        size_pt = font_size_pt + _HEADING_SIZE_BUMP_PT.get(role, 0)

        paragraph.paragraph_format.line_spacing = line_spacing
        for run in paragraph.runs:
            _set_run_font(run, font_family)
            run.font.size = Pt(size_pt)
            run.font.bold = role in _HEADING_ROLES

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(output_path))

    return [
        f"set page margins to {margins_mm['top']}/{margins_mm['bottom']}/"
        f"{margins_mm['left']}/{margins_mm['right']}mm (top/bottom/left/right)",
        f"applied {font_family} {font_size_pt}pt, line spacing {line_spacing} to body text",
        "bolded and enlarged heading paragraphs per classified role",
    ]
