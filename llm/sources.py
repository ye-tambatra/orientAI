"""
Parses source citations out of rag/retriever.py's formatted context blocks
so they can be surfaced to callers separately from the model's prose reply.

Each block retrieve_context() produces looks like:
    [Source: {original_file}, ID: {source_id}]
    Title: {title} (Section)
    Content:
    ...
"""

import json
import re
from pathlib import Path

# Tool names (llm/tools.py) whose return value may contain retrieve_context()
# citation blocks worth surfacing as sources.
RAG_TOOL_NAMES = {
    "rechercher_formation",
    "verifier_prerequis",
    "comparer_parcours",
    "rechercher_competences",
    "expliquer_recommandation",
}

_SOURCE_BLOCK_RE = re.compile(
    r"\[Source: (?P<file>[^,]+), ID: (?P<id>[^\]]+)\]\s*\n"
    r"Title: (?P<title>[^\n(]+)"
)

_SOURCES_JSON_PATH = Path("data/structured/sources.json")


def _load_source_urls() -> dict[str, str | None]:
    """Maps source_id -> url (or None) from data/structured/sources.json."""
    try:
        entries = json.loads(_SOURCES_JSON_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {entry["id"]: entry.get("url") for entry in entries}


_SOURCE_URLS = _load_source_urls()


def parse_sources(text: str) -> list[dict[str, str | None]]:
    """Extracts unique {source_id, file, title, url} dicts from a context string.

    `url` is the original web page/document URL from sources.json (None for
    sources that don't have one, e.g. the PDF exam schedule).
    """
    sources: dict[str, dict[str, str | None]] = {}
    for match in _SOURCE_BLOCK_RE.finditer(text):
        source_id = match.group("id").strip()
        sources[source_id] = {
            "source_id": source_id,
            "file": match.group("file").strip(),
            "title": match.group("title").strip(),
            "url": _SOURCE_URLS.get(source_id),
        }
    return list(sources.values())
