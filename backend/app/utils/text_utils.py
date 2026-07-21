"""Conservative text normalization for identity search, never formula mutation."""

import unicodedata


def normalize_search_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()
