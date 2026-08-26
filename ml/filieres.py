"""Grounded metadata about the 16 ISPM filières.

This is the label space of the ML model (`code`) and the basis for the
synthetic-data generator's ground truth (`matieres`, `mots_cles`).

Provenance
----------
`matieres` for IGGLIA, ESIIA, IMTICIA, ISAIA, CAA, FIC, DTJA, EMP, EMII,
GCA, ICMP, TEH come verbatim from data/structured/lectures_list.md
(scraped from the ISPM exam-schedule PDF, source SRC004 in
data/structured/sources.json).

`nom` / `departement` come from data/structured/page_ispm_filiere.md
(source SRC002/SRC003).

IAA, PIP, AEE and TEE were NOT present in the scraped first-year lecture
list (only a shared "BIO 1" trunk was found, and no TEE-specific list).
Their `matieres` lists below are therefore an ASSUMPTION made for the sole
purpose of feature-engineering the ML model (they are never shown to a
user as an official fact — the RAG/tool layer is the only source allowed
to state official curriculum facts). This is called out again in
ml/synthetic.py's generation-method documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Filiere:
    code: str
    nom: str
    departement: str
    matieres: tuple[str, ...]
    mots_cles: tuple[str, ...]  # interests/keywords used to match free-text
    environnement: str  # dominant type of work environment
    assumed_matieres: bool = False  # True if matieres is a hypothesis, not scraped


FILIERES: dict[str, Filiere] = {
    f.code: f
    for f in [
        Filiere(
            code="IGGLIA",
            nom="Informatique de Gestion, Génie Logiciel et Intelligence Artificielle",
            departement="Informatique et Télécommunication",
            matieres=(
                "Math Fi", "Comptabilité", "Algèbre", "Français",
                "Informatique scientifique", "TP Informatique", "HTML/CSS",
                "Analyse", "Bases de données", "Algorithmes", "PASCAL",
                "Organisation", "Structures de données",
                "Probabilités-Statistiques", "Math Discrètes",
            ),
            mots_cles=("informatique", "gestion", "génie logiciel", "programmation",
                       "intelligence artificielle", "bases de données", "entreprise"),
            environnement="bureau",
        ),
        Filiere(
            code="ESIIA",
            nom="Electronique Système Informatique et Intelligence Artificielle",
            departement="Informatique et Télécommunication",
            matieres=(
                "Electronique", "Structure des Ordinateurs", "Electricité",
                "Algèbre", "TP Informatique", "Français", "Informatique Scientifique",
                "HTML/CSS", "Analyse", "Bases de données", "Algorithmes", "PASCAL",
                "Structures de données", "Probabilités-Statistiques", "Math Discrètes",
            ),
            mots_cles=("électronique", "réseaux", "systèmes", "télécommunication",
                       "informatique", "matériel", "intelligence artificielle"),
            environnement="atelier",
        ),
        Filiere(
            code="IMTICIA",
            nom="Informatique Multimédia Technologie de L'information et de la "
                "Communication et Intelligence Artificielle",
            departement="Informatique et Télécommunication",
            matieres=(
                "NTT", "PAO", "Son", "Algèbre", "Français", "Informatique Scientifique",
                "HTML/CSS", "Analyse", "Bases de données", "Algorithmes",
                "TP Informatique", "PASCAL", "Télécom", "Structures de données",
                "Probabilités-Statistiques", "Math Discrètes",
            ),
            mots_cles=("multimédia", "design", "communication", "télécommunication",
                       "informatique", "création", "audiovisuel"),
            environnement="bureau",
        ),
        Filiere(
            code="ISAIA",
            nom="Informatique Statistique Appliquée et Intelligence Artificielle",
            departement="Informatique et Télécommunication",
            matieres=(
                "Combinatoire et Probabilités", "Macroéconomie", "Algèbre", "Français",
                "Informatique Scientifique", "HTML/CSS", "Analyse", "Bases de données",
                "Algorithmes", "Microéconomie", "PASCAL", "TP Informatique",
                "Structures de données", "Statistique Appliquée", "Math Discrètes",
            ),
            mots_cles=("statistique", "données", "mathématiques", "économie",
                       "intelligence artificielle", "analyse de données", "informatique"),
            environnement="bureau",
        ),
        Filiere(
            code="CAA",
            nom="Commerce et Administration des Affaires",
            departement="Techniques des Affaires",
            matieres=(
                "Anglais", "Math Fi", "Stratégie", "Informatique", "Français",
                "Mathématiques G.", "Techniques d'accueil", "Bureautique", "Droit",
                "Probabilités", "Statistique", "Organisation", "Comptabilité",
                "Marketing", "Allemand", "Economie",
            ),
            mots_cles=("commerce", "marketing", "vente", "négociation", "affaires",
                       "management", "gestion"),
            environnement="bureau",
        ),
        Filiere(
            code="FIC",
            nom="Finances et Comptabilités",
            departement="Techniques des Affaires",
            matieres=(
                "Anglais", "Math Fi", "Stratégie", "Informatique",
                "Institutions Financières", "Français", "Analyse Mathématique",
                "Choix d'investissement", "Bureautique", "Droit commercial",
                "Probabilités", "Finance d'entreprise", "Statistique", "Organisation",
                "Comptabilité Fi", "Marketing", "Allemand", "Economie",
            ),
            mots_cles=("finance", "comptabilité", "banque", "chiffres", "investissement",
                       "gestion"),
            environnement="bureau",
        ),
        Filiere(
            code="DTJA",
            nom="Droit et Techniques Juridiques des Affaires",
            departement="Techniques des Affaires",
            matieres=(
                "Anglais", "Droit Civil", "Droit Constitutionnel", "Informatique",
                "Français", "Introduction au droit", "HIE", "Bureautique", "HPE",
                "Logique", "Introduction au droit administratif", "Organisation",
                "R. I.", "Marketing", "Allemand", "Economie",
            ),
            mots_cles=("droit", "juridique", "justice", "administration", "loi"),
            environnement="bureau",
        ),
        Filiere(
            code="EMP",
            nom="Economie et Management de Projet",
            departement="Techniques des Affaires",
            matieres=(
                "Anglais", "Math Fi", "Stratégie", "Informatique", "Macroéconomie",
                "Français", "Analyse Mathématique", "HIE", "Bureautique", "HPE",
                "Probabilités", "Microéconomie", "Statistique", "Organisation",
                "Comptabilité", "Marketing", "Allemand",
            ),
            mots_cles=("économie", "management", "projet", "planification", "analyse"),
            environnement="bureau",
        ),
        Filiere(
            code="IAA",
            nom="Industrie Agroalimentaire",
            departement="Biotechnologie et Agronomie",
            matieres=(
                "Génétique", "Biochimie", "Microbiologie", "Chimie Organique",
                "Analyse Mathématique", "Biologie Cellulaire", "Statistique",
                "Informatique", "Français", "Physiologie Animale", "Physiologie Végétale",
            ),
            mots_cles=("agroalimentaire", "industrie", "qualité", "production",
                       "biologie", "chimie"),
            environnement="laboratoire",
            assumed_matieres=True,
        ),
        Filiere(
            code="PIP",
            nom="Pharmacologie et Industries Pharmaceutiques",
            departement="Biotechnologie et Agronomie",
            matieres=(
                "Biochimie", "Chimie Organique", "Microbiologie", "Génétique",
                "Physiologie Animale", "Biologie Cellulaire", "Analyse Mathématique",
                "Statistique", "Informatique", "Français",
            ),
            mots_cles=("pharmacie", "médicament", "santé", "plantes médicinales",
                       "chimie", "biologie", "laboratoire"),
            environnement="laboratoire",
            assumed_matieres=True,
        ),
        Filiere(
            code="AEE",
            nom="Agriculture et Elevage",
            departement="Biotechnologie et Agronomie",
            matieres=(
                "Biologie Végétale", "Biologie animale", "Physiologie Végétale",
                "Physiologie Animale", "Génétique", "Chimie Organique",
                "Analyse Mathématique", "Statistique", "Informatique", "Français",
            ),
            mots_cles=("agriculture", "élevage", "rural", "agri-business",
                       "nature", "environnement", "biologie"),
            environnement="terrain",
            assumed_matieres=True,
        ),
        Filiere(
            code="EMII",
            nom="Electro-Mécanique et Informatique Industrielle",
            departement="Génie Industriel et Génie Civil",
            matieres=(
                "Mécanique Générale", "FM", "OM", "Algèbre", "Français", "Electricité",
                "Informatique", "Analyse", "RDM", "Electronique", "Dessin",
                "Mécanique des fluides", "MCI", "AUTOCAD", "Mécanique Rationnelle",
            ),
            mots_cles=("mécanique", "électricité", "industrie", "machines",
                       "informatique industrielle", "technique"),
            environnement="atelier",
        ),
        Filiere(
            code="GCA",
            nom="Génie Civil et Architecture",
            departement="Génie Industriel et Génie Civil",
            matieres=(
                "Mécanique Générale", "MDC", "Géologie Appliquée", "Algèbre", "Français",
                "RDM", "Informatique", "Analyse", "Technologie des bâtiments", "Métré",
                "Dessin", "Hydraulique", "Topographie", "TP Topographie",
            ),
            mots_cles=("construction", "architecture", "bâtiment", "urbanisme",
                       "dessin", "génie civil"),
            environnement="terrain",
        ),
        Filiere(
            code="ICMP",
            nom="Industries Chimiques, Minières et Pétrolières",
            departement="Génie Industriel et Génie Civil",
            matieres=(
                "Mécanique Générale", "Chimie Minérale", "Mines", "Algèbre", "Français",
                "Géodynamique Minière", "Informatique", "Analyse", "RDM", "Atomistique",
                "Dessin", "Mécanique des fluides", "AUTOCAD", "Chimie Organique",
            ),
            mots_cles=("chimie", "mines", "pétrole", "industrie", "géologie"),
            environnement="terrain",
        ),
        Filiere(
            code="TEE",
            nom="Tourisme et Environnement",
            departement="Techniques du Tourisme",
            matieres=(
                "Anglais", "Environnement", "Sites touristiques", "Informatique",
                "Français", "Ecologie Animale", "Hygiène", "Nutrition humaine",
                "Organisation", "Flore", "Marketing", "Allemand", "Economie",
            ),
            mots_cles=("tourisme", "environnement", "nature", "faune", "flore",
                       "écologie", "voyage"),
            environnement="terrain",
            assumed_matieres=True,
        ),
        Filiere(
            code="TEH",
            nom="Tourisme et Hôtellerie",
            departement="Techniques du Tourisme",
            matieres=(
                "Anglais", "Environnement", "Sites touristiques", "Informatique",
                "Français", "Techniques d'agence", "Techniques d'accueil", "Bureautique",
                "Ecologie Animale", "Hygiène", "Nutrition humaine", "Art Culinaire",
                "Science des aliments", "Organisation", "Flore", "Marketing",
                "Allemand", "Economie",
            ),
            mots_cles=("tourisme", "hôtellerie", "accueil", "cuisine", "voyage",
                       "restauration", "contact clientèle"),
            environnement="contact_client",
        ),
    ]
}

FILIERE_CODES: tuple[str, ...] = tuple(FILIERES.keys())
