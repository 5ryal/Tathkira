"""Normalise an informal Arabic request into clean input for drafting."""

import re
from dataclasses import dataclass

MAX_REQUEST_LENGTH = 2000

_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670]")
_TATWEEL = "\u0640"
_ALEF_FORMS = str.maketrans({"\u0623": "\u0627", "\u0625": "\u0627", "\u0622": "\u0627"})
_ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_WHITESPACE_RUN = re.compile(r"\s+")


@dataclass
class NormalisedRequest:
    """A request kept in both its original and cleaned form."""

    original: str
    normalised: str


def normalise_request(text: str) -> NormalisedRequest:
    """Clean an informal Arabic request while keeping the original text."""
    if not text.strip():
        raise ValueError("empty request")
    if len(text) > MAX_REQUEST_LENGTH:
        raise ValueError("request too long")

    cleaned = _DIACRITICS.sub("", text)
    cleaned = cleaned.replace(_TATWEEL, "")
    cleaned = cleaned.translate(_ALEF_FORMS)
    cleaned = cleaned.translate(_ARABIC_INDIC_DIGITS)
    cleaned = _WHITESPACE_RUN.sub(" ", cleaned).strip()
    return NormalisedRequest(original=text, normalised=cleaned)
