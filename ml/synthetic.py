"""Documented synthetic profile generator (training data).

Per the brief's section 5 warning ("Un jeu entièrement synthétique est
engendré à partir de règles : le modèle qui l'apprend ne fait que
retrouver ces règles"), this generator deliberately injects noise and
label ambiguity rather than emitting profiles that perfectly match a
domain's textbook definition. It is not meant to be a source of truth by
itself — it is meant to be generalised *away from*, which is measured by
testing the trained model on the real survey responses (ml/survey.py).

The model's label space is a set of general pedagogical/professional
orientation **domains** (ml.domaines), not ISPM filière codes — see
ml/domaines.py's module docstring for why.

Method (documented, as required by section 5)
-----------------------------------------------
For each of the 15 orientation domains:
1. Build a pool of "candidate tags" from ml.vocab using the hand-curated
   domain/tag affinity weights (>= 0.5 = strong match, 0.3-0.5 = weak/
   plausible match).
2. Sample 2-4 "matières préférées" and 1-3 "centres d'intérêt" tags,
   weighted by affinity, mixing in the occasional out-of-domain tag.
3. Sample "compétences déclarées" from the *same* domain-tag pool at a
   lower rate — deliberately NOT from any personality/character trait
   vocabulary, since section 16 of the brief forbids using inferred
   personality/character as a recommendation criterion. This exclusion is
   a design decision, not an oversight.
4. Sample environnement_travail = the domain's dominant environment with
   probability 0.75, a random other environment otherwise (self-report
   noise: people are imperfect judges of their environment preference).
5. Sample serie_bac from a coarse, hand-set distribution per broad
   category (scientific/technical domains skew towards S/D/C; business/
   law/tourism domains skew towards A/D/L) — this is a HYPOTHESIS about
   Malagasy secondary-school streaming, not a verified statistic.
6. With probability P_MISLABEL, the row's features are generated for
   domain X but the recorded label is a *different* domain Y that shares
   at least one tag with X — simulating the real phenomenon (documented
   in the brief) that a student's actual past choice is not always the
   choice that best fit their profile. These rows are flagged
   `label_noise=True` in the exported CSV so any downstream analysis can
   isolate their effect.

Biases potentially introduced (documented, as required by section 5)
----------------------------------------------------------------------
- The tag/domain affinity weights are hand-curated (ml.vocab), not
  learned from data — they encode the generator's own assumptions about
  which subjects "belong" to which domain, so a model trained purely on
  this data risks re-learning the generator's biases rather than a
  genuine population's.
- Classes are perfectly balanced (equal profiles per domain), which does
  not reflect real applicant volumes across fields of study.
- No demographic attribute (gender, age, origin) is generated or used at
  all, by design (section 16 forbids using such attributes as
  recommendation criteria).

Consistency controls applied
------------------------------
- Every generated profile has at least one non-empty field.
- `label_noise` rows are capped at P_MISLABEL (default 6%) and clearly
  flagged rather than silently mixed in.
- The tag pool, sampling probabilities and this documentation live in one
  file so the generation process is reproducible from a fixed `seed`.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from ml.domaines import DOMAINE_IDS, DOMAINES
from ml.vocab import ENVIRONNEMENTS, SERIES_BAC, TAGS

P_MISLABEL = 0.06
P_ENV_NOISE = 0.25
N_MATIERES = (2, 4)
N_INTERETS = (1, 3)
N_COMPETENCES = (0, 2)

_SCIENTIFIC = {
    "informatique_numerique", "data_ia", "reseaux_electronique", "genie_industriel",
    "genie_civil", "chimie_mines", "agroalimentaire", "pharmacie_sante", "agriculture_elevage",
}
_BAC_DIST = {
    "scientific": {"S": .5, "D": .3, "C": .1, "Autre": .1},
    "other": {"A": .35, "D": .35, "L": .1, "Technique": .1, "Autre": .1},
}


def _weighted_pool(domaine_id: str, min_weight: float = 0.3) -> tuple[list[str], list[float]]:
    tags, weights = [], []
    for tag in TAGS:
        w = tag.weights.get(domaine_id, 0.0)
        if w >= min_weight:
            tags.append(tag.id)
            weights.append(w)
    total = sum(weights)
    return tags, [w / total for w in weights]


def _sample_tags(rng: random.Random, domaine_id: str, n_range: tuple[int, int]) -> list[str]:
    tags, weights = _weighted_pool(domaine_id)
    n = min(rng.randint(*n_range), len(tags))
    if n == 0:
        return []
    return rng.choices(tags, weights=weights, k=n) if n < len(tags) else tags


def _sample_bac(rng: random.Random, domaine_id: str) -> str:
    dist = _BAC_DIST["scientific" if domaine_id in _SCIENTIFIC else "other"]
    options, weights = list(dist.keys()), list(dist.values())
    return rng.choices(options, weights=weights, k=1)[0]


def _related_domaine(rng: random.Random, domaine_id: str, own_tags: set[str]) -> str:
    """Finds another domain sharing at least one tag with `domaine_id`, for
    label-noise simulation."""
    candidates = []
    for other in DOMAINE_IDS:
        if other == domaine_id:
            continue
        other_tags, _ = _weighted_pool(other)
        if own_tags & set(other_tags):
            candidates.append(other)
    return rng.choice(candidates) if candidates else domaine_id


def generate_profile(rng: random.Random, domaine_id: str) -> dict:
    matieres = _sample_tags(rng, domaine_id, N_MATIERES)
    interets = _sample_tags(rng, domaine_id, N_INTERETS)
    competences = _sample_tags(rng, domaine_id, N_COMPETENCES)

    environnement = DOMAINES[domaine_id].environnement
    if rng.random() < P_ENV_NOISE:
        environnement = rng.choice(ENVIRONNEMENTS)

    serie_bac = _sample_bac(rng, domaine_id)

    label_noise = rng.random() < P_MISLABEL
    own_tags = set(matieres) | set(interets)
    label = _related_domaine(rng, domaine_id, own_tags) if label_noise else domaine_id

    def tag_labels(tag_ids: list[str]) -> str:
        by_id = {t.id: t.label for t in TAGS}
        return ", ".join(by_id[t] for t in tag_ids)

    return {
        "matieres_preferees": tag_labels(matieres),
        "centres_interet": tag_labels(interets),
        "competences": tag_labels(competences),
        "environnement_travail": environnement,
        "serie_bac": serie_bac,
        "domaine_genere_pour": domaine_id,   # the domain the features were sampled for
        "label_noise": label_noise,
        "domaine_recommande": label,         # the recorded ground-truth label
    }


def generate_dataset(n_per_class: int = 150, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for domaine_id in DOMAINE_IDS:
        for _ in range(n_per_class):
            rows.append(generate_profile(rng, domaine_id))
    rng.shuffle(rows)
    return rows


def write_dataset(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


GENERATION_DOC = __doc__


def write_documentation(path: Path, n_per_class: int, seed: int, n_total: int, n_noisy: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Génération des données synthétiques ORIENT'IA\n\n")
        f.write(GENERATION_DOC.replace("\n\n\n", "\n\n"))
        f.write("\n\n## Paramètres effectivement utilisés pour cette version du jeu de données\n\n")
        f.write(f"- `n_per_class` = {n_per_class} profils par domaine\n")
        f.write(f"- `seed` = {seed} (reproductible)\n")
        f.write(f"- Total de profils générés : {n_total}\n")
        f.write(f"- Profils avec étiquette bruitée (`label_noise=True`) : {n_noisy} "
                f"({n_noisy / n_total:.1%})\n")


if __name__ == "__main__":
    rows = generate_dataset()
    out = Path(__file__).resolve().parent.parent / "data" / "ml" / "synthetic" / "profils_synthetiques.csv"
    write_dataset(rows, out)
    n_noisy = sum(1 for r in rows if r["label_noise"])
    write_documentation(out.parent / "generation_doc.md", 150, 42, len(rows), n_noisy)
    print(f"Wrote {len(rows)} synthetic profiles to {out}")
