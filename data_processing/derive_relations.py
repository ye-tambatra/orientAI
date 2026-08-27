"""Dérive les relations compétence→métiers et parcours→métiers (indicatif),
pour compléter la catégorie "relations entre compétences, parcours et
métiers" demandée par le sujet (section 3).

Pourquoi une dérivation et pas un scraping
-------------------------------------------
Aucune page du site ISPM ne publie de table compétence→métier ou
parcours→métier (vérifié le 27/08/2026, voir derive_competences.py pour la
même vérification côté compétences). Il n'y a donc rien à extraire d'une
source officielle ici non plus.

Ce script chaîne deux inférences déjà documentées :
1. Parcours → Compétences (data_processing/derive_competences.py, table
   matière→compétence).
2. Compétence → Métiers typiques (table ci-dessous, connaissance générale
   des intitulés de métiers francophones — PAS une donnée spécifique à
   l'ISPM).

Le résultat (Parcours → Métiers, obtenu par transitivité) est donc une
DOUBLE inférence, encore plus éloignée d'un fait vérifié que les
compétences seules. Le fichier généré le dit explicitement en en-tête et
par section, et `llm/tools.py` (identifier_debouches) doit présenter ce
contenu comme une piste à vérifier, jamais comme un débouché confirmé par
l'ISPM.

Reproductibilité : `python -m data_processing.derive_relations` régénère
`data/structured/relations_competences_metiers.md` à partir de
`ml/filieres.py` et de la table ci-dessous (aucune dépendance réseau).
"""

from __future__ import annotations

from data_processing.derive_competences import MATIERE_TO_COMPETENCE, derive_competences
from ml.filieres import FILIERES

OUTPUT_MD = "data/structured/relations_competences_metiers.md"

# Compétence (famille générique) -> métiers typiquement associés à ce type
# de compétence dans le monde francophone. Volontairement large et
# illustratif : ce n'est ni un référentiel métier officiel, ni propre à
# Madagascar ou à l'ISPM.
COMPETENCE_TO_METIERS: dict[str, tuple[str, ...]] = {
    "Programmation et développement logiciel": (
        "Développeur logiciel", "Ingénieur informatique", "Développeur web",
    ),
    "Usage professionnel de l'informatique": (
        "Assistant(e) de gestion", "Employé de bureau polyvalent",
    ),
    "Conception et gestion de bases de données": (
        "Administrateur de bases de données", "Data analyst",
    ),
    "Raisonnement mathématique et modélisation": (
        "Analyste quantitatif", "Enseignant de mathématiques",
    ),
    "Analyse statistique et probabiliste": (
        "Data scientist", "Statisticien", "Analyste de données",
    ),
    "Gestion financière et comptable": (
        "Comptable", "Contrôleur de gestion", "Analyste financier",
    ),
    "Analyse économique": (
        "Économiste", "Chargé d'études économiques",
    ),
    "Management et organisation d'entreprise": (
        "Chef de projet", "Responsable d'exploitation", "Manager d'équipe",
    ),
    "Marketing et relation commerciale": (
        "Chargé de marketing", "Commercial", "Responsable communication",
    ),
    "Communication écrite et orale": (
        "Chargé de communication", "Rédacteur", "Assistant de direction",
    ),
    "Communication en langue étrangère": (
        "Interprète/traducteur", "Assistant export",
    ),
    "Analyse juridique": (
        "Juriste d'entreprise", "Assistant juridique", "Conseiller juridique",
    ),
    "Électronique et systèmes embarqués": (
        "Ingénieur électronique", "Technicien télécom",
        "Ingénieur systèmes embarqués",
    ),
    "Création et production multimédia": (
        "Designer multimédia", "Monteur audiovisuel",
        "Chargé de production numérique",
    ),
    "Mécanique et technologies industrielles": (
        "Technicien de maintenance industrielle", "Ingénieur mécanique",
        "Responsable de production",
    ),
    "Dessin technique et conception assistée": (
        "Dessinateur-projeteur", "Technicien CAO/DAO",
    ),
    "Génie civil et construction": (
        "Ingénieur génie civil", "Conducteur de travaux", "Architecte",
    ),
    "Chimie et sciences des matériaux": (
        "Technicien de laboratoire", "Ingénieur chimiste",
        "Contrôleur qualité",
    ),
    "Géologie et exploitation minière": (
        "Géologue", "Ingénieur des mines", "Technicien minier",
    ),
    "Biologie et sciences du vivant": (
        "Technicien de laboratoire biomédical", "Ingénieur agroalimentaire",
        "Chercheur en biotechnologie",
    ),
    "Gestion environnementale et écotourisme": (
        "Guide écotouristique", "Chargé de projets environnementaux",
        "Agent de conservation",
    ),
    "Hôtellerie, restauration et accueil": (
        "Responsable d'hôtellerie", "Chef cuisinier",
        "Agent d'accueil touristique",
    ),
}


def metiers_indicatifs_pour_filiere(matieres: tuple[str, ...], max_metiers: int = 12) -> list[str]:
    """Union des métiers associés aux compétences déduites d'une filière,
    dédupliqués, plafonnés à `max_metiers` pour rester lisible.

    Round-robin sur les compétences (un métier de chacune à tour de rôle)
    plutôt que d'épuiser une compétence avant de passer à la suivante : les
    compétences sont triées alphabétiquement (derive_competences), donc un
    simple troncage aurait systématiquement favorisé les compétences
    commençant par une lettre précoce (ex: "Analyse...") au détriment de
    compétences tout aussi centrales pour la filière (ex: "Programmation..."
    pour IGGLIA) — vérifié, c'est exactement ce qui s'est produit avant ce
    correctif.
    """
    competences = derive_competences(matieres)
    par_competence = [
        [m for m in COMPETENCE_TO_METIERS.get(c, ())] for c in competences
    ]
    metiers: list[str] = []
    round_index = 0
    while len(metiers) < max_metiers and any(par_competence):
        for metiers_c in par_competence:
            if round_index < len(metiers_c):
                m = metiers_c[round_index]
                if m not in metiers:
                    metiers.append(m)
                if len(metiers) >= max_metiers:
                    break
        if all(round_index >= len(metiers_c) for metiers_c in par_competence):
            break
        round_index += 1
    return metiers[:max_metiers]


def main() -> None:
    lines = [
        "# Relations compétences → métiers, et parcours → métiers (indicatif)",
        "",
        "> **Double inférence, PAS une donnée officielle ISPM.** Ce fichier "
        "chaîne deux déductions : matières→compétences (voir "
        "`competences_par_filiere.md`) puis compétences→métiers (table de "
        "métiers francophones génériques, sans lien spécifique avec l'ISPM "
        "ou Madagascar). Aucune page du site ISPM ne publie de liste "
        "compétence→métier ou parcours→métier (vérifié le 27/08/2026). À "
        "présenter à l'utilisateur comme des pistes indicatives à vérifier, "
        "jamais comme des débouchés confirmés par l'ISPM.",
        "",
        "## Compétence → Métiers typiques (déduit)",
        "",
    ]
    for competence, metiers in COMPETENCE_TO_METIERS.items():
        lines.append(f"### {competence}")
        lines.append("")
        for m in metiers:
            lines.append(f"- {m}")
        lines.append("")

    lines.append("## Parcours → Métiers indicatifs (déduit, transitif via les compétences)")
    lines.append("")
    for code, filiere in FILIERES.items():
        metiers = metiers_indicatifs_pour_filiere(filiere.matieres)
        lines.append(f"### {filiere.nom} ({code})")
        lines.append("")
        lines.append("**Métiers indicatifs (déduits, non officiels, à vérifier) :**")
        lines.append("")
        for m in metiers:
            lines.append(f"- {m}")
        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Dérivation terminée. Résultats dans {OUTPUT_MD}")


if __name__ == "__main__":
    main()
