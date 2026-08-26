"""Turns a candidate profile (a plain dict) into the numeric feature vector
consumed by ml.models.

A profile is a plain dict with the following optional keys (all optional —
the encoder degrades gracefully to zeros/uniform for anything missing,
which is what lets the conversational agent call the model progressively
as it learns more about the user, per spec section 9 "recueillir
progressivement le profil"):

    matieres_preferees:    str | list[str]  (free text, comma-separated ok)
    competences:           str | list[str]
    centres_interet:       str | list[str]
    environnement_travail: str  (one of ml.vocab.ENVIRONNEMENTS, free text ok)
    serie_bac:             str  (one of ml.vocab.SERIES_BAC, free text ok)

The same encoder is used for synthetic profiles, real survey rows and live
user profiles built by the conversational agent, so the model always sees
a consistent feature space.
"""

from __future__ import annotations

import numpy as np

from ml.vocab import ENVIRONNEMENTS, SERIES_BAC, TAG_IDS, normalize_free_text, strip_accents

# Weight given to each free-text field when merging into the tag vector.
# Interests and preferred subjects are the strongest signal; declared
# competences are informative but noisier self-assessment, so weighted less.
_FIELD_WEIGHTS = {
    "matieres_preferees": 1.0,
    "centres_interet": 1.0,
    "competences": 0.6,
}

FEATURE_NAMES: list[str] = (
    [f"tag:{t}" for t in TAG_IDS]
    + [f"env:{e}" for e in ENVIRONNEMENTS]
    + [f"bac:{b}" for b in SERIES_BAC]
)


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _match_categorical(value: str, options: tuple[str, ...]) -> str | None:
    if not value:
        return None
    norm_value = strip_accents(value).lower()
    for opt in options:
        if strip_accents(opt).lower() in norm_value:
            return opt
    return None


def tags_from_profile(profile: dict) -> dict[str, float]:
    """Returns {tag_id: weight in [0, 1]} merged across the free-text fields."""
    scores: dict[str, float] = {}
    for field, weight in _FIELD_WEIGHTS.items():
        text = _as_text(profile.get(field))
        for tag_id in normalize_free_text(text):
            scores[tag_id] = max(scores.get(tag_id, 0.0), weight)
    return scores


def encode_profile(profile: dict) -> np.ndarray:
    """Profile dict -> dense float32 vector of length len(FEATURE_NAMES)."""
    vec = np.zeros(len(FEATURE_NAMES), dtype=np.float32)

    tag_scores = tags_from_profile(profile)
    for i, tag_id in enumerate(TAG_IDS):
        vec[i] = tag_scores.get(tag_id, 0.0)

    offset = len(TAG_IDS)
    env = _match_categorical(_as_text(profile.get("environnement_travail")), ENVIRONNEMENTS)
    if env is not None:
        vec[offset + ENVIRONNEMENTS.index(env)] = 1.0

    offset += len(ENVIRONNEMENTS)
    bac = _match_categorical(_as_text(profile.get("serie_bac")), SERIES_BAC)
    if bac is not None:
        vec[offset + SERIES_BAC.index(bac)] = 1.0

    return vec


def encode_batch(profiles: list[dict]) -> np.ndarray:
    return np.stack([encode_profile(p) for p in profiles]) if profiles else np.zeros((0, len(FEATURE_NAMES)))
