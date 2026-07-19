from pathlib import Path

from docx import Document

from app.pipeline.schemas import ClassifiedParagraph, ParagraphRole


def validate_document(
    output_path: Path, classified: list[ClassifiedParagraph], rules: dict
) -> list[str]:
    document = Document(str(output_path))
    issues: list[str] = []

    expected_margins_mm = rules["margins_mm"]
    section = document.sections[0]
    actual_margins_mm = {
        "top": round(section.top_margin.mm),
        "bottom": round(section.bottom_margin.mm),
        "left": round(section.left_margin.mm),
        "right": round(section.right_margin.mm),
    }
    for side, expected in expected_margins_mm.items():
        actual = actual_margins_mm[side]
        if actual != expected:
            issues.append(f"{side} margin is {actual}mm, expected {expected}mm")

    font_family = rules["font_family"]
    font_size_pt = rules["font_size_pt"]
    role_by_index = {paragraph.index: paragraph.role for paragraph in classified}

    for index, paragraph in enumerate(document.paragraphs):
        role = role_by_index.get(index, ParagraphRole.BODY)
        if role != ParagraphRole.BODY:
            continue

        for run in paragraph.runs:
            if run.font.name != font_family:
                issues.append(
                    f"paragraph {index}: font is {run.font.name!r}, expected {font_family!r}"
                )
            if run.font.size is not None and round(run.font.size.pt) != font_size_pt:
                issues.append(
                    f"paragraph {index}: size is {run.font.size.pt}pt, expected {font_size_pt}pt"
                )

    return issues
