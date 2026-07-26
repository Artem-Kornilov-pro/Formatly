import pytest
from pydantic import ValidationError

from app.pipeline.rules import FormattingRules


def test_defaults_match_gost_conventions_when_nothing_is_specified():
    rules = FormattingRules.model_validate({})

    assert rules.font_family == "Times New Roman"
    assert rules.font_size_pt == 14
    assert rules.line_spacing == 1.5
    assert rules.margins_mm.top == 20
    assert rules.margins_mm.left == 30
    assert rules.bold_headings is True
    assert rules.center_headings is True
    assert rules.italic_headings is False
    assert rules.paragraph_alignment == "justify"
    assert rules.paragraph_indent_enabled is True
    assert rules.paragraph_indent_mm == 12.5
    assert rules.page_break_before_heading_1 is False


def test_a_profile_can_override_a_single_field_and_keep_the_rest_default():
    rules = FormattingRules.model_validate({"center_headings": False})

    assert rules.center_headings is False
    # everything else still falls back to its default
    assert rules.font_family == "Times New Roman"
    assert rules.bold_headings is True


def test_margins_can_be_partially_overridden():
    rules = FormattingRules.model_validate({"margins_mm": {"left": 25}})

    assert rules.margins_mm.left == 25
    assert rules.margins_mm.top == 20  # untouched default


def test_rejects_an_invalid_paragraph_alignment():
    with pytest.raises(ValidationError):
        FormattingRules.model_validate({"paragraph_alignment": "diagonal"})
