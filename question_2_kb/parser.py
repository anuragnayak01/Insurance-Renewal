"""
Ingestion layer for Question 2.

Handles:
- Web page extraction (strip nav/header/footer boilerplate)
- PDF text extraction with failure flagging
- Terminology / date standardization
- PII detection and masking
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

logger = logging.getLogger("kb_ingest")

# Tags that are almost never content in an insurer marketing/FAQ page.
BOILERPLATE_TAGS = ["nav", "footer", "header", "script", "style", "form", "aside"]

# Phrases that show up as page furniture, not policy content.
BOILERPLATE_PHRASES = [
    "terms of use",
    "privacy policy",
    "all rights reserved",
    "contact us",
    "cookie policy",
    "subscribe to our newsletter",
]

# Canonical term map — collapse inconsistent vendor/marketing language
# down to the terms the voice agent's prompts actually use.
TERMINOLOGY_MAP = {
    r"\bpolicy\s*holder\b": "policyholder",
    r"\bpremia\b": "premiums",
    r"\bT&C'?s?\b": "terms and conditions",
    r"\brenewal\s*wndow\b": "renewal window",  # example typo-normalization
    r"\bgrace\s*-?\s*period\b": "grace period",
}

# ISO-normalize common date phrasings so "12/01/2026", "Jan 12 2026",
# and "12th January 2026" don't fragment retrieval as different facts.
DATE_PATTERNS = [
    (re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"), r"\3-\2-\1"),  # DD/MM/YYYY -> YYYY-MM-DD (adjust per source locale)
]

PII_PATTERNS = {
    "policy_id": re.compile(r"\b[A-Z]{2}-\d{4}-\d{5,8}\b"),
    "phone_in": re.compile(r"(?<!\d)\+91[-\s]?[6-9]\d{9}\b|\b[6-9]\d{9}\b"),
    "phone_generic": re.compile(r"\b\+?1?\d{10}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "card_or_account": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{0,4}\b"),
}

PII_LABELS = {
    "policy_id": "[REDACTED_POLICY_ID]",
    "phone_in": "[REDACTED_PHONE]",
    "phone_generic": "[REDACTED_PHONE]",
    "email": "[REDACTED_EMAIL]",
    "card_or_account": "[REDACTED_ACCOUNT]",
}


@dataclass
class ExtractionResult:
    success: bool
    text: str = ""
    source: str = ""
    error: Optional[str] = None
    contains_pii_removed: bool = False
    flags: list = field(default_factory=list)


class DataCleaner:
    @staticmethod
    def clean_text(raw_text: str) -> str:
        cleaned = " ".join(raw_text.split())
        for phrase in BOILERPLATE_PHRASES:
            cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def standardize_terminology(text: str) -> str:
        for pattern, replacement in TERMINOLOGY_MAP.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def standardize_dates(text: str) -> str:
        for pattern, replacement in DATE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    @staticmethod
    def mask_pii(text: str) -> tuple[str, bool]:
        """Returns (masked_text, pii_was_found)."""
        found = False
        for key, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                found = True
                text = pattern.sub(PII_LABELS[key], text)
        return text, found


class WebExtractor:
    @staticmethod
    def extract(url: str, timeout: int = 10) -> ExtractionResult:
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "kb-ingest/1.0"})
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Extraction failed for %s: %s", url, e)
            return ExtractionResult(success=False, source=url, error=str(e), flags=["fetch_failed"])

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in BOILERPLATE_TAGS:
            for el in soup.find_all(tag):
                el.decompose()

        raw_text = soup.get_text(separator=" ")
        cleaned = DataCleaner.clean_text(raw_text)

        flags = []
        if len(cleaned) < 200:
            # Very short extraction usually means the page was JS-rendered
            # and BeautifulSoup only saw an empty shell — flag it instead
            # of silently ingesting near-nothing.
            flags.append("suspiciously_short_extraction")

        return ExtractionResult(success=True, text=cleaned, source=url, flags=flags)


class PdfExtractor:
    @staticmethod
    def extract(path: str) -> ExtractionResult:
        try:
            reader = PdfReader(path)
        except Exception as e:
            logger.warning("Failed to open PDF %s: %s", path, e)
            return ExtractionResult(success=False, source=path, error=str(e), flags=["open_failed"])

        pages_text = []
        empty_pages = 0
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception as e:
                logger.warning("Failed to extract page %d of %s: %s", i, path, e)
                text = ""
            if not text.strip():
                empty_pages += 1
            pages_text.append(text)

        full_text = DataCleaner.clean_text(" ".join(pages_text))

        flags = []
        if empty_pages > 0:
            # Empty pages usually mean scanned/image-only pages with no OCR —
            # flag rather than silently dropping content.
            flags.append(f"{empty_pages}_page(s)_returned_no_text_possible_scan")
        if not full_text.strip():
            return ExtractionResult(success=False, source=path, error="No extractable text", flags=flags)

        return ExtractionResult(success=True, text=full_text, source=path, flags=flags)


def process_document(extraction: ExtractionResult) -> ExtractionResult:
    """Run the shared cleaning pipeline (terminology, dates, PII) on an already-extracted doc."""
    if not extraction.success:
        return extraction

    text = DataCleaner.standardize_terminology(extraction.text)
    text = DataCleaner.standardize_dates(text)
    text, pii_found = DataCleaner.mask_pii(text)

    extraction.text = text
    extraction.contains_pii_removed = pii_found
    return extraction
