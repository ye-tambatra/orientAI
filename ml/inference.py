"""Inference-time wrapper: loads the trained artifact and exposes the
operations the conversational agent needs (brief section 8: "Intégration
obligatoire du modèle" — analyser_profil / classer_parcours /
calculer_adequation / identifier_points_forts), plus a quantitative
`expliquer_recommandation` used to answer the demo question "Pourquoi
ton modèle recommande-t-il ce parcours ?".

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
from ml.features import FEATURE_NAMES, encode_profile
from ml.models import SoftmaxRegression, model_from_dict
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
        self.model = model_from_dict(data["model"])

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
        explanation = self.expliquer_recommandation(profile, top_n=top_n)
        return [c["label"] for c in explanation["contributions"] if c["contribution"] > 0]

    @staticmethod
    def _feature_label(feature_name: str) -> str:
        kind, value = feature_name.split(":", 1)
        if kind == "tag":
            return get_tag(value).label
        if kind == "env":
            return f"Environnement de travail souhaité : {value}"
        if kind == "bac":
            return f"Série de bac : {value}"
        return feature_name

    def expliquer_recommandation(self, profile: dict, domaine_id: str | None = None,
                                  top_n: int = 5) -> dict:
        """Quantitative, auditable explanation of a domain's score for a
        profile: for every DECLARED element (subject/interest/competence
        tag, série de bac, environnement souhaité), its exact contribution
        to that domain's pre-softmax score (learned weight × presence in
        the profile), sorted by contribution.

        This directly answers the brief's demo question "Pourquoi ton
        modèle recommande-t-il ce parcours ?" with real numbers traced
        back to what the model actually learned — not a generated
        rationalisation. Elements the user did NOT declare contribute
        zero and are omitted; character/personality is never a candidate
        feature (brief section 16) so it can never appear here.

        Args:
            profile: The profile dict (see ml.features.encode_profile).
            domaine_id: Explain this specific domain; defaults to the
                model's own top-1 prediction for this profile.
            top_n: How many of the strongest contributions to return.
        """
        if not isinstance(self.model, SoftmaxRegression):
            # ml/train.py always deploys SoftmaxRegression specifically
            # because it is the only one of the 3 compared architectures
            # with per-feature weights to explain from — see ml/train.py's
            # "Deployed model" comment. This branch should be unreachable
            # in practice; it exists so a future change to what gets
            # deployed fails loudly here instead of on a wrong attribute.
            raise ModelNotTrainedError(
                f"Le modèle déployé ({type(self.model).__name__}) ne "
                "supporte pas l'explication par contribution de variable "
                "(réservée à SoftmaxRegression). Relancer `python -m "
                "ml.train`, qui déploie toujours SoftmaxRegression."
            )
        x = encode_profile(profile)
        if domaine_id is None:
            top = self.rank_domaines(profile, k=1)
            if not top:
                return {"domaine": None, "score": None, "contributions": []}
            domaine_id = top[0]["domaine"]
        class_index = self.classes.index(domaine_id)

        contributions = []
        for i, feature_name in enumerate(FEATURE_NAMES):
            if x[i] == 0:
                continue
            weight = float(self.model.W[i, class_index])
            contributions.append({
                "label": self._feature_label(feature_name),
                "valeur_declaree": True,
                "poids_appris": round(weight, 4),
                "contribution": round(weight * float(x[i]), 4),
            })
        contributions.sort(key=lambda c: c["contribution"], reverse=True)

        proba = self.model.predict_proba(x.reshape(1, -1))[0][class_index]
        return {
            "domaine": domaine_id,
            "label": DOMAINES[domaine_id].label,
            "score": round(float(proba), 4),
            "biais_du_modele": round(float(self.model.b[class_index]), 4),
            "contributions": contributions[:top_n],
        }


@lru_cache(maxsize=1)
def get_model() -> OrientationModel:
    return OrientationModel()
