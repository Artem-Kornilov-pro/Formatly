from pathlib import Path

from docx import Document

from app.pipeline.schemas import ParsedParagraph


def parse_docx(path: Path) -> list[ParsedParagraph]:
    document = Document(str(path))

    return [
        ParsedParagraph(
            index=index,
            text=paragraph.text,
            style_name=paragraph.style.name if paragraph.style else "Normal",
        )
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.text.strip()
    ]
