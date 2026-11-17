"""Tests for the normalise step (specs/normalise/SPEC.md)."""

import pytest

from tathkira.agent.normalise import NormalisedRequest, normalise_request


# --- Acceptance criteria ---------------------------------------------------


def test_acceptance_mixed_request_is_cleaned() -> None:
    """The spec's worked example is normalised and its original is kept."""
    raw = "  ابي  أسترجع كلمةُ السر بسرعة ١٠ ثواني  "
    result = normalise_request(raw)
    assert result.normalised == "ابي استرجع كلمة السر بسرعة 10 ثواني"
    assert result.original == raw


def test_acceptance_english_words_are_kept() -> None:
    """English words inside an Arabic request are left untouched."""
    result = normalise_request("ابي صفحة login جديدة")
    assert result.normalised == "ابي صفحة login جديدة"


def test_returns_normalised_request_dataclass() -> None:
    """The return value is the NormalisedRequest dataclass with both fields."""
    result = normalise_request("ابي تقرير")
    assert isinstance(result, NormalisedRequest)
    assert result.original == "ابي تقرير"
    assert result.normalised == "ابي تقرير"


# --- Rule 1: remove diacritics -------------------------------------------


def test_removes_tashkeel_marks() -> None:
    """Tashkeel marks in U+064B-U+0652 are removed."""
    assert normalise_request("كَتَبَ المُطَوِّر").normalised == "كتب المطور"


def test_removes_superscript_alef() -> None:
    """U+0670 is removed even though it sits outside U+064B-U+0652."""
    assert normalise_request("هٰذا").normalised == "هذا"


def test_removes_every_diacritic_in_range() -> None:
    """Every mark from U+064B to U+0652 plus U+0670 is stripped."""
    marks = "".join(chr(code) for code in range(0x064B, 0x0653)) + "\u0670"
    assert normalise_request("ب" + marks + "ت").normalised == "بت"


def test_keeps_marks_outside_the_diacritic_range() -> None:
    """U+0653 is outside the specified range and therefore kept."""
    assert normalise_request("ا\u0653بي").normalised == "ا\u0653بي"


# --- Rule 2: remove tatweel ---------------------------------------------


def test_removes_tatweel() -> None:
    """Tatweel U+0640 is removed from inside words."""
    assert normalise_request("ابـــي").normalised == "ابي"


# --- Rule 3: unify alef forms --------------------------------------------


def test_unifies_alef_forms() -> None:
    """Alef with hamza above, below and madda all become plain alef."""
    assert normalise_request("أحمد إبراهيم آدم").normalised == "احمد ابراهيم ادم"


def test_keeps_plain_alef() -> None:
    """A plain alef is not changed."""
    assert normalise_request("احمد").normalised == "احمد"


# --- Rule 4: Arabic-Indic digits ----------------------------------------


def test_converts_arabic_indic_digits() -> None:
    """Each Arabic-Indic digit becomes its Western counterpart."""
    assert normalise_request("٠١٢٣٤٥٦٧٨٩").normalised == "0123456789"


def test_keeps_western_digits() -> None:
    """Western digits are left as they are."""
    assert normalise_request("10 ثواني").normalised == "10 ثواني"


# --- Rule 5: whitespace --------------------------------------------------


def test_collapses_whitespace_runs() -> None:
    """Spaces, tabs and line breaks collapse into single spaces."""
    assert normalise_request("ابي\n\nصفحة\t\tجديدة   الان").normalised == "ابي صفحة جديدة الان"


def test_trims_leading_and_trailing_whitespace() -> None:
    """Surrounding spaces are trimmed from the normalised text."""
    assert normalise_request("   ابي تقرير   ").normalised == "ابي تقرير"


# --- Rule 6: unchanged characters ---------------------------------------


def test_keeps_taa_marbuta_and_alef_maqsura() -> None:
    """ة and ى are left exactly as they are."""
    assert normalise_request("مدرسة على").normalised == "مدرسة على"


# --- Error contract -----------------------------------------------------


def test_empty_string_raises() -> None:
    """An empty string is rejected with the spec's message."""
    with pytest.raises(ValueError) as excinfo:
        normalise_request("")
    assert str(excinfo.value) == "empty request"


def test_whitespace_only_raises() -> None:
    """Whitespace-only input is rejected with the spec's message."""
    with pytest.raises(ValueError) as excinfo:
        normalise_request("   ")
    assert str(excinfo.value) == "empty request"


def test_newlines_only_raises() -> None:
    """Line breaks alone still count as an empty request."""
    with pytest.raises(ValueError) as excinfo:
        normalise_request("\n\t\n")
    assert str(excinfo.value) == "empty request"


def test_over_limit_raises() -> None:
    """2001 characters are rejected with the spec's message."""
    with pytest.raises(ValueError) as excinfo:
        normalise_request("ا" * 2001)
    assert str(excinfo.value) == "request too long"


# --- Boundary cases -----------------------------------------------------


def test_exactly_2000_characters_is_accepted() -> None:
    """Exactly 2000 characters are accepted and unchanged."""
    text = "ا" * 2000
    result = normalise_request(text)
    assert result.original == text
    assert result.normalised == text


def test_length_is_measured_on_the_original() -> None:
    """A request over 2000 characters is rejected even if cleaning shortens it."""
    text = "ا" * 1990 + "\u064B" * 20
    assert len(text) == 2010
    with pytest.raises(ValueError) as excinfo:
        normalise_request(text)
    assert str(excinfo.value) == "request too long"


# --- Determinism --------------------------------------------------------


def test_is_deterministic() -> None:
    """The same input always produces the same output."""
    first = normalise_request("  ابي  تقريرُ  ")
    second = normalise_request("  ابي  تقريرُ  ")
    assert first == second
    assert first.normalised == "ابي تقرير"
