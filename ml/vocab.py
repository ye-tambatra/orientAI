"""Canonical vocabulary shared by the synthetic generator, the survey
normaliser and the feature encoder.

Design choice: rather than maintaining three separate lists (matières,
compétences, centres d'intérêt), free text collected in any of those three
profile fields is normalised against the *same* pool of ~24 canonical
tags. Each tag carries a hand-curated affinity weight per general
orientation **domain** (ml.domaines — NOT per ISPM filière: the ML label
space is a general pedagogical-orientation taxonomy, reusable outside of
ISPM; the ISPM-filière lookup is a separate, later step — see
ml/domaines.py's module docstring). This single pool is used to:

1. generate synthetic profiles (sample tags weighted by a target domain),
2. normalise real survey free text into the same tag space,
3. build the multi-hot feature vector consumed by the models.

Weights are a documented modelling *hypothesis*, not a verified fact —
see ml/synthetic.py's generation-method note and the evaluation report's
"biais et limites" section.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _norm(text: str) -> str:
    return strip_accents(text).lower().strip()


@dataclass(frozen=True)
class Tag:
    id: str
    label: str
    synonyms: tuple[str, ...]
    weights: dict[str, float]  # domaine_id -> affinity in [0, 1]


TAGS: tuple[Tag, ...] = (
    Tag("informatique_prog", "Informatique / Programmation",
        ("informatique", "programmation", "algorithmique", "developpement", "code", "logiciel"),
        {"informatique_numerique": .9, "reseaux_electronique": .7, "data_ia": .8, "genie_industriel": .3}),
    Tag("intelligence_artificielle", "Intelligence artificielle",
        ("intelligence artificielle", " ia ", "machine learning", "data science", "ia,", "ia."),
        {"data_ia": .9, "informatique_numerique": .8, "reseaux_electronique": .6}),
    Tag("reseaux_systemes", "Réseaux / Systèmes",
        ("reseau", "systeme", "telecommunication", "telecom", "serveur"),
        {"reseaux_electronique": .9, "informatique_numerique": .6}),
    Tag("mathematiques", "Mathématiques",
        ("mathematique", "math,", "math.", "algebre", "analyse mathematique"),
        {"data_ia": .9, "informatique_numerique": .6, "genie_industriel": .5, "genie_civil": .5,
         "chimie_mines": .5, "finance_comptabilite": .5, "economie_management": .5}),
    Tag("statistiques_donnees", "Statistiques / Données",
        ("statistique", "donnees", "analyse de donnees", "probabilite"),
        {"data_ia": .95, "finance_comptabilite": .5, "economie_management": .4, "informatique_numerique": .4}),
    Tag("physique_electronique", "Physique / Electronique",
        ("physique", "electronique", "electricite"),
        {"reseaux_electronique": .9, "genie_industriel": .8, "chimie_mines": .3}),
    Tag("mecanique_industrie", "Mécanique / Industrie",
        ("mecanique", "industrie", "machines", "usine"),
        {"genie_industriel": .9, "chimie_mines": .5, "genie_civil": .3}),
    Tag("genie_civil_archi", "Génie civil / Architecture",
        ("genie civil", "architecture", "construction", "batiment", "dessin technique", "topographie"),
        {"genie_civil": .95}),
    Tag("chimie", "Chimie",
        ("chimie",),
        {"chimie_mines": .7, "pharmacie_sante": .6, "agroalimentaire": .5}),
    Tag("mines_geologie", "Mines / Géologie",
        ("mines", "geologie", "petrol"),
        {"chimie_mines": .9}),
    Tag("biologie_sante", "Biologie / Santé",
        ("biologie", "sante", "physiologie", "genetique", "microbiologie"),
        {"pharmacie_sante": .8, "agroalimentaire": .6, "agriculture_elevage": .5}),
    Tag("pharmacie_medicament", "Pharmacie / Médicament",
        ("pharmacie", "medicament", "pharmacologie"),
        {"pharmacie_sante": .95}),
    Tag("agriculture_elevage", "Agriculture / Elevage",
        ("agriculture", "elevage", "rural", "agronomie", "agri-business", "agribusiness"),
        {"agriculture_elevage": .95, "agroalimentaire": .4}),
    Tag("agroalimentaire", "Agroalimentaire",
        ("agroalimentaire", "alimentaire", "qualite produit"),
        {"agroalimentaire": .9}),
    Tag("gestion_entreprise", "Gestion / Entreprise",
        ("gestion", "management", "organisation", "entreprise"),
        {"informatique_numerique": .5, "commerce_gestion": .6, "economie_management": .6, "finance_comptabilite": .4}),
    Tag("commerce_marketing", "Commerce / Marketing",
        ("commerce", "marketing", "vente", "negociation", "affaires"),
        {"commerce_gestion": .9, "economie_management": .4}),
    Tag("finance_comptabilite", "Finance / Comptabilité",
        ("finance", "comptabilite", "banque", "investissement"),
        {"finance_comptabilite": .95, "commerce_gestion": .3}),
    Tag("droit_juridique", "Droit / Juridique",
        ("droit", "juridique", "justice", " loi"),
        {"droit": .95}),
    Tag("economie", "Economie",
        ("economie", "macroeconomie", "microeconomie"),
        {"economie_management": .9, "data_ia": .4, "commerce_gestion": .3}),
    Tag("multimedia_design", "Multimédia / Design",
        ("multimedia", "design", "creation", "audiovisuel", "graphisme", " son", "pao"),
        {"informatique_numerique": .95}),
    Tag("communication", "Communication",
        ("communication",),
        {"informatique_numerique": .5, "commerce_gestion": .4, "hotellerie_restauration": .4}),
    Tag("tourisme_environnement", "Tourisme / Environnement",
        ("tourisme", "environnement", "nature", "ecologie", "faune", "flore", "voyage"),
        {"tourisme_environnement": .9, "hotellerie_restauration": .5}),
    Tag("hotellerie_accueil", "Hôtellerie / Accueil",
        ("hotellerie", "accueil", "cuisine", "restauration", "art culinaire", "clientele"),
        {"hotellerie_restauration": .95}),
    Tag("langues", "Langues étrangères",
        ("anglais", "allemand", "langues"),
        {"commerce_gestion": .3, "finance_comptabilite": .3, "droit": .3, "economie_management": .3,
         "tourisme_environnement": .3, "hotellerie_restauration": .4}),
)

TAG_IDS: tuple[str, ...] = tuple(t.id for t in TAGS)
_TAG_BY_ID: dict[str, Tag] = {t.id: t for t in TAGS}

ENVIRONNEMENTS: tuple[str, ...] = (
    "bureau", "atelier", "laboratoire", "terrain", "contact_client",
)

SERIES_BAC: tuple[str, ...] = ("S", "D", "C", "A", "L", "Technique", "Autre")


def tags_for_domaine(domaine_id: str, threshold: float = 0.55) -> list[str]:
    """Tags whose affinity with `domaine_id` is at least `threshold`."""
    return [t.id for t in TAGS if t.weights.get(domaine_id, 0.0) >= threshold]


def normalize_free_text(text: str) -> list[str]:
    """Splits a comma-separated free-text answer and maps each token to the
    canonical tag ids whose synonyms appear in it.

    Unmatched tokens (e.g. "Autre") are silently dropped: they carry no
    exploitable signal for the model, but are preserved verbatim in the raw
    survey export/registry for transparency.
    """
    if not text:
        return []
    found: set[str] = set()
    normalized_text = f" {_norm(text)} "
    for tag in TAGS:
        for syn in tag.synonyms:
            if _norm(syn) in normalized_text:
                found.add(tag.id)
                break
    return sorted(found)


def get_tag(tag_id: str) -> Tag:
    return _TAG_BY_ID[tag_id]
