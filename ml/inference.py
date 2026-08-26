"""Inference-time wrapper: loads the trained artifact and exposes the
three operations the conversational agent needs (brief section 8:
"Intégration obligatoire du modèle" — analyser_profil / classer_parcours /
calculer_adequation / identifier_points_forts).

The model predicts a general pedagogical/professional orientation
**domain** (ml.domaines), not directly an ISPM filière — see
ml/domaines.py's module docstring for why. `rank_domaines` therefore
returns, for each predicted domain, both the ML score and the domain's
looked-up candidate ISPM filière(s) — the latter is a fixed table, not a
model prediction, and is clearly labelled as such so the assistant can
keep provenance separate (section 8's requirement to distinguish model
output from document output from LLM prose). Concrete facts about an ISPM
filière (débouchés, prérequis...) must still come from the RAG layer.

This is the ONLY module llm/tools.py should import from ml/.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

from ml.domaines import DOMAINES
from ml.features import encode_profile, tags_from_profile
from ml.models import SoftmaxRegression
from ml.vocab import get_tag

ARTIFACT_PATH = Path(__file__).resolve().parent / "artifacts" / "model.json"

PROVENANCE_LABEL = "Modèle ML ORIENT'IA (régression softmax, entraîné sur données synthétiques)"


class ModelNotTrainedError(RuntimeError):
    pass


class OrientationModel:
    def __init__(self, artifact_path: Path = ARTIFACT_PATH):
        if not artifact_path.exists():
            raise ModelNotTrainedError(
                f"Aucun modèle entraîné trouvé à {artifact_path}. "
                "Lancer `python -m ml.train` avant d'utiliser l'assistant."
            )
        with open(artifact_path, encoding="utf-8") as f:
            data = json.load(f)
        self.classes = data["classes"]
        self.model = SoftmaxRegression.from_dict(data["softmax_regression"])

    def rank_domaines(self, profile: dict, k: int = 3) -> list[dict]:
        """Returns the top-k orientation domains ranked by predicted
        adequacy, each with a 0-1 score and its looked-up candidate ISPM
        filières. This is `classer_parcours` / `analyser_profil` from the
        brief's example tool list, generalised to a domain rather than a
        single ISPM filière."""
        x = encode_profile(profile).reshape(1, -1)
        proba = self.model.predict_proba(x)[0]
        order = np.argsort(-proba)[:k]
        return [
            {
                "domaine": self.classes[i],
                "label": DOMAINES[self.classes[i]].label,
                "score": round(float(proba[i]), 4),
                "filieres_ispm_correspondantes": list(DOMAINES[self.classes[i]].ispm_filieres),
            }
            for i in order
        ]

    def score_adequation(self, profile: dict, domaine_id: str) -> dict:
        """`calculer_score_adequation` / `calculer_adequation` from the brief."""
        domaine_id = domaine_id.strip().lower().replace(" ", "_")
        if domaine_id not in DOMAINES:
            return {"error": f"Domaine inconnu : {domaine_id!r}. Domaines valides : {sorted(DOMAINES)}"}
        x = encode_profile(profile).reshape(1, -1)
        proba = self.model.predict_proba(x)[0]
        class_index = self.classes.index(domaine_id)
        rank = int(np.argsort(-proba).tolist().index(class_index)) + 1
        return {
            "domaine": domaine_id,
            "label": DOMAINES[domaine_id].label,
            "score": round(float(proba[class_index]), 4),
            "rang_parmi_domaines": rank,
            "nb_domaines": len(self.classes),
            "filieres_ispm_correspondantes": list(DOMAINES[domaine_id].ispm_filieres),
        }

    def points_forts(self, profile: dict, top_n: int = 3) -> list[str]:
        """`identifier_points_forts`: which declared tags line up with the
        model's top prediction, i.e. a coarse, linear-model explanation
        (the softmax weight of each active tag for the predicted class) —
        NOT a personality inference, only a readout of user-declared
        subjects/interests/competences (brief section 16 compliance)."""
        tag_scores = tags_from_profile(profile)
        if not tag_scores:
            return []
        top = self.rank_domaines(profile, k=1)
        if not top:
            return []
        predicted_domaine = top[0]["domaine"]
        class_index = self.classes.index(predicted_domaine)

        from ml.vocab import TAG_IDS
        contributions = []
        for tag_id, presence in tag_scores.items():
            i = TAG_IDS.index(tag_id)
            weight = self.model.W[i, class_index]
            contributions.append((tag_id, weight * presence))
        contributions.sort(key=lambda t: t[1], reverse=True)
        return [get_tag(tag_id).label for tag_id, w in contributions[:top_n] if w > 0]


@lru_cache(maxsize=1)
def get_model() -> OrientationModel:
    return OrientationModel()
