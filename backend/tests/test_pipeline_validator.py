from pathlib import Path

from docx import Document
from docx.shared import Mm, Pt

from app.pipeline.formatter import apply_formatting
from app.pipeline.schemas import ClassifiedParagraph, ParagraphRole
from app.pipeline.validator import validate_document

RULES = {
    "font_family": "Times New Roman",
    "font_size_pt": 14,
    "line_spacing": 1.5,
    "margins_mm": {"top": 20, "bottom": 20, "left": 30, "right": 15},
}


def test_validate_document_reports_no_issues_after_formatter_ran(tmp_path: Path):
    document = Document()
    document.add_heading("Introduction", level=1)
    document.add_paragraph("Body paragraph.")
    input_path = tmp_path / "input.docx"
    document.save(str(input_path))

    output_path = tmp_path / "output.docx"
    classified = [
        ClassifiedParagraph(index=0, text="Introduction", role=ParagraphRole.HEADING_1),
        ClassifiedParagraph(index=1, text="Body paragraph.", role=ParagraphRole.BODY),
    ]
    apply_formatting(input_path, output_path, classified, RULES)

    issues = validate_document(output_path, classified, RULES)

    assert issues == []


def test_validate_document_flags_wrong_margins(tmp_path: Path):
    document = Document()
    document.add_paragraph("Body paragraph.")
    for section in document.sections:
        section.top_margin = Mm(10)
    path = tmp_path / "wrong_margins.docx"
    document.save(str(path))

    issues = validate_document(path, classified=[], rules=RULES)

    assert any("top margin" in issue for issue in issues)


def test_validate_document_flags_wrong_body_font_and_size(tmp_path: Path):
    document = Document()
    paragraph = document.add_paragraph("Body paragraph.")
    for section in document.sections:
        section.top_margin = Mm(RULES["margins_mm"]["top"])
        section.bottom_margin = Mm(RULES["margins_mm"]["bottom"])
        section.left_margin = Mm(RULES["margins_mm"]["left"])
        section.right_margin = Mm(RULES["margins_mm"]["right"])
    run = paragraph.runs[0]
    run.font.name = "Calibri"
    run.font.size = Pt(11)
    path = tmp_path / "wrong_font.docx"
    document.save(str(path))

    classified = [ClassifiedParagraph(index=0, text="Body paragraph.", role=ParagraphRole.BODY)]
    issues = validate_document(path, classified, RULES)

    assert any("font is 'Calibri'" in issue for issue in issues)
    assert any("size is 11" in issue for issue in issues)


def test_validate_document_ignores_heading_paragraphs_for_body_font_check(tmp_path: Path):
    document = Document()
    paragraph = document.add_heading("Introduction", level=1)
    for section in document.sections:
        section.top_margin = Mm(RULES["margins_mm"]["top"])
        section.bottom_margin = Mm(RULES["margins_mm"]["bottom"])
        section.left_margin = Mm(RULES["margins_mm"]["left"])
        section.right_margin = Mm(RULES["margins_mm"]["right"])
    paragraph.runs[0].font.name = "Calibri"
    path = tmp_path / "heading_only.docx"
    document.save(str(path))

    classified = [ClassifiedParagraph(index=0, text="Introduction", role=ParagraphRole.HEADING_1)]
    issues = validate_document(path, classified, RULES)

    assert issues == []
