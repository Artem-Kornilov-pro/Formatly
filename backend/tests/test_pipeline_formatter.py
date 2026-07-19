from pathlib import Path

from docx import Document

from app.pipeline.formatter import apply_formatting
from app.pipeline.schemas import ClassifiedParagraph, ParagraphRole

RULES = {
    "font_family": "Times New Roman",
    "font_size_pt": 14,
    "line_spacing": 1.5,
    "margins_mm": {"top": 20, "bottom": 20, "left": 30, "right": 15},
}


def _build_input(tmp_path: Path) -> Path:
    document = Document()
    document.add_heading("Introduction", level=1)
    document.add_paragraph("Body paragraph in Calibri.")
    path = tmp_path / "input.docx"
    document.save(str(path))
    return path


def test_apply_formatting_sets_margins_font_and_line_spacing(tmp_path: Path):
    input_path = _build_input(tmp_path)
    output_path = tmp_path / "output.docx"
    classified = [
        ClassifiedParagraph(index=0, text="Introduction", role=ParagraphRole.HEADING_1),
        ClassifiedParagraph(index=1, text="Body paragraph in Calibri.", role=ParagraphRole.BODY),
    ]

    changes = apply_formatting(input_path, output_path, classified, RULES)

    assert output_path.exists()
    assert len(changes) == 3

    result = Document(str(output_path))
    section = result.sections[0]
    assert round(section.top_margin.mm) == 20
    assert round(section.left_margin.mm) == 30
    assert round(section.right_margin.mm) == 15

    heading_run = result.paragraphs[0].runs[0]
    assert heading_run.font.name == "Times New Roman"
    assert heading_run.font.size.pt == 16  # 14 + heading_1 bump of 2
    assert heading_run.font.bold is True

    body_paragraph = result.paragraphs[1]
    assert body_paragraph.paragraph_format.line_spacing == 1.5
    body_run = body_paragraph.runs[0]
    assert body_run.font.name == "Times New Roman"
    assert body_run.font.size.pt == 14
    assert body_run.font.bold is not True


def test_apply_formatting_defaults_unclassified_paragraphs_to_body(tmp_path: Path):
    input_path = _build_input(tmp_path)
    output_path = tmp_path / "output.docx"

    # no classification supplied for either paragraph
    apply_formatting(input_path, output_path, classified=[], rules=RULES)

    result = Document(str(output_path))
    for paragraph in result.paragraphs:
        for run in paragraph.runs:
            assert run.font.size.pt == 14
            assert run.font.bold is not True


def test_apply_formatting_sets_cyrillic_capable_font_attributes(tmp_path: Path):
    document = Document()
    document.add_paragraph("Привет, Formatly!")
    input_path = tmp_path / "input.docx"
    document.save(str(input_path))
    output_path = tmp_path / "output.docx"

    apply_formatting(input_path, output_path, classified=[], rules=RULES)

    result = Document(str(output_path))
    run = result.paragraphs[0].runs[0]
    rpr = run._element.find(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr"
    )
    rfonts = rpr.find(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts"
    )
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    assert rfonts.get(f"{ns}eastAsia") == "Times New Roman"
    assert rfonts.get(f"{ns}hAnsi") == "Times New Roman"
