"""General pedagogical/professional orientation domains.

This is the ML model's actual label space. It intentionally does NOT
mirror the 16 ISPM filière codes one-for-one: the model's job is to infer
a candidate's general orientation (the kind of question a student or
lycéen asks regardless of which school they end up in — "quel domaine me
correspond ?"), not to arbitrate between ISPM's own internal
curriculum-organisation choices (e.g. ISPM splits "informatique" into
four differently-flavoured filières that a 17-year-old profile usually
cannot distinguish yet: IGGLIA vs IMTICIA vs ISAIA vs ESIIA all look like
"j'aime l'informatique et l'IA").

`ISPM_FILIERES` on each Domaine is therefore a separate, hand-curated
*lookup* — not something the model predicts — used by the conversational
tools to bridge "the model says this general domain fits you" to "here
are the matching ISPM filières, go check their details via the
documents/RAG". This keeps the ML component genuinely about pedagogical
orientation, reusable outside of ISPM, while the assistant still ends up
recommending concrete ISPM filières as the brief's mission requires
(section 2: "une orientation personnalisée à partir [...] des formations
de l'ISPM").
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Domaine:
    id: str
    label: str
    description: str
    environnement: str  # dominant work environment, used by the synthetic generator
    ispm_filieres: tuple[str, ...]  # candidate ISPM filière codes (lookup, not predicted)


DOMAINES: dict[str, Domaine] = {
    d.id: d
    for d in [
        Domaine(
            "informatique_numerique",
            "Informatique & Numérique (développement, gestion, multimédia)",
            "Conception de logiciels, applications de gestion, sites et supports multimédias.",
            "bureau",
            ("IGGLIA", "IMTICIA"),
        ),
        Domaine(
            "data_ia",
            "Data Science, Statistique & Intelligence Artificielle",
            "Analyse de données, modélisation statistique, intelligence artificielle appliquée.",
            "bureau",
            ("ISAIA", "IGGLIA"),
        ),
        Domaine(
            "reseaux_electronique",
            "Réseaux, Électronique & Systèmes",
            "Matériel informatique, télécommunications, systèmes et réseaux.",
            "atelier",
            ("ESIIA",),
        ),
        Domaine(
            "genie_industriel",
            "Génie Industriel, Mécanique & Électrotechnique",
            "Mécanique, électricité industrielle, maintenance et informatique industrielle.",
            "atelier",
            ("EMII",),
        ),
        Domaine(
            "genie_civil",
            "Génie Civil & Architecture",
            "Construction, bâtiment, urbanisme et architecture.",
            "terrain",
            ("GCA",),
        ),
        Domaine(
            "chimie_mines",
            "Chimie, Mines & Industries Pétrolières",
            "Chimie industrielle, exploitation minière et pétrolière.",
            "terrain",
            ("ICMP",),
        ),
        Domaine(
            "commerce_gestion",
            "Commerce, Marketing & Gestion des Affaires",
            "Vente, négociation, marketing et administration des entreprises.",
            "bureau",
            ("CAA",),
        ),
        Domaine(
            "finance_comptabilite",
            "Finance & Comptabilité",
            "Comptabilité, gestion financière, institutions financières.",
            "bureau",
            ("FIC",),
        ),
        Domaine(
            "droit",
            "Droit & Techniques Juridiques",
            "Droit des affaires, droit civil et administratif.",
            "bureau",
            ("DTJA",),
        ),
        Domaine(
            "economie_management",
            "Économie & Management de Projet",
            "Analyse économique, gestion et pilotage de projets.",
            "bureau",
            ("EMP",),
        ),
        Domaine(
            "agroalimentaire",
            "Agroalimentaire",
            "Transformation et qualité des produits alimentaires.",
            "laboratoire",
            ("IAA",),
        ),
        Domaine(
            "pharmacie_sante",
            "Pharmacie & Santé",
            "Pharmacologie, industries pharmaceutiques, santé.",
            "laboratoire",
            ("PIP",),
        ),
        Domaine(
            "agriculture_elevage",
            "Agriculture & Élevage",
            "Production agricole, élevage, agri-business.",
            "terrain",
            ("AEE",),
        ),
        Domaine(
            "tourisme_environnement",
            "Tourisme & Environnement",
            "Valorisation touristique du patrimoine naturel et culturel.",
            "terrain",
            ("TEE",),
        ),
        Domaine(
            "hotellerie_restauration",
            "Hôtellerie & Restauration",
            "Accueil, art culinaire, gestion hôtelière.",
            "contact_client",
            ("TEH",),
        ),
    ]
}

DOMAINE_IDS: tuple[str, ...] = tuple(DOMAINES.keys())
