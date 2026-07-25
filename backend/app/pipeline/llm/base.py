from typing import Protocol

from app.pipeline.schemas import ClassifiedParagraph, ParsedParagraph


class ParagraphClassifier(Protocol):
    """The only thing the pipeline depends on for classification.

    Swapping the underlying AI provider means writing a new class that
    implements this method - nothing else in the pipeline changes.
    """

    def classify(self, paragraphs: list[ParsedParagraph]) -> list[ClassifiedParagraph]: ...
