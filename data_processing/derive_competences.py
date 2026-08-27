"""Dérive une liste de "compétences développées" par filière, à partir des
matières déjà scrapées dans ml/filieres.py (elles-mêmes issues de
data/structured/lectures_list.md, source SRC004).

Pourquoi ce script existe
--------------------------
Le sujet (section 3, "Constitution du corpus pédagogique") demande une liste
de "compétences développées" distincte des matières. Vérification faite le
27/08/2026 (WebFetch sur https://ispm-edu.com/filieres.php et
/presentation.php) : le site officiel de l'ISPM ne publie AUCUNE liste de
compétences séparée des matières/objectifs généraux. Il n'y a donc rien à
scraper de plus — inventer une liste "officielle" violerait la règle du
sujet ("Une information non vérifiée ne devra pas être présentée comme une
information officielle").

Ce script produit à la place une inférence documentée : chaque matière est
rattachée à une famille de compétences générique (ex: "Algorithmes" →
"Programmation et développement logiciel"), et le résultat par filière est
la liste dédupliquée des familles couvertes par ses matières.

Le fichier généré (data/structured/competences_par_filiere.md) est marqué
explicitement comme une DÉDUCTION, pas une donnée officielle ISPM — voir son
en-tête, sources.json (SRC005, status "interne (dérivé)"), et le docstring
de rechercher_competences dans llm/tools.py qui instruit le LLM à toujours
distinguer les deux devant l'utilisateur.

Reproductibilité : `python data_processing/derive_competences.py` régénère
le fichier à partir de ml/filieres.py (aucune dépendance réseau).
"""

from __future__ import annotations

from ml.filieres import FILIERES

OUTPUT_MD = "data/structured/competences_par_filiere.md"

# Mapping matière -> famille de compétence générique. Volontairement
# grossier (une matière = une compétence transversale plausible) : ce n'est
# pas un référentiel pédagogique officiel, seulement une aide de lecture
# pour l'utilisateur et pour rechercher_competences.
MATIERE_TO_COMPETENCE: dict[str, str] = {
    # Informatique / développement
    "Algorithmes": "Programmation et développement logiciel",
    "PASCAL": "Programmation et développement logiciel",
    "HTML/CSS": "Programmation et développement logiciel",
    "Structures de données": "Programmation et développement logiciel",
    "TP Informatique": "Programmation et développement logiciel",
    "Informatique scientifique": "Programmation et développement logiciel",
    "Informatique Scientifique": "Programmation et développement logiciel",
    "Informatique": "Usage professionnel de l'informatique",
    "Bases de données": "Conception et gestion de bases de données",
    "Bureautique": "Usage professionnel de l'informatique",
    # Mathématiques / quantitatif
    "Algèbre": "Raisonnement mathématique et modélisation",
    "Analyse": "Raisonnement mathématique et modélisation",
    "Analyse Mathématique": "Raisonnement mathématique et modélisation",
    "Mathématiques G.": "Raisonnement mathématique et modélisation",
    "Math Discrètes": "Raisonnement mathématique et modélisation",
    "Combinatoire et Probabilités": "Analyse statistique et probabiliste",
    "Probabilités": "Analyse statistique et probabiliste",
    "Probabilités-Statistiques": "Analyse statistique et probabiliste",
    "Statistique": "Analyse statistique et probabiliste",
    "Statistique Appliquée": "Analyse statistique et probabiliste",
    # Finance / comptabilité
    "Comptabilité": "Gestion financière et comptable",
    "Comptabilité Fi": "Gestion financière et comptable",
    "Math Fi": "Gestion financière et comptable",
    "Finance d'entreprise": "Gestion financière et comptable",
    "Choix d'investissement": "Gestion financière et comptable",
    "Institutions Financières": "Gestion financière et comptable",
    # Économie / management
    "Economie": "Analyse économique",
    "Macroéconomie": "Analyse économique",
    "Microéconomie": "Analyse économique",
    "Organisation": "Management et organisation d'entreprise",
    "Stratégie": "Management et organisation d'entreprise",
    "Marketing": "Marketing et relation commerciale",
    "HIE": "Management et organisation d'entreprise",
    "HPE": "Management et organisation d'entreprise",
    "Techniques d'accueil": "Marketing et relation commerciale",
    "Techniques d'agence": "Marketing et relation commerciale",
    # Langues
    "Français": "Communication écrite et orale",
    "Anglais": "Communication en langue étrangère",
    "Allemand": "Communication en langue étrangère",
    # Droit
    "Droit": "Analyse juridique",
    "Droit Civil": "Analyse juridique",
    "Droit Constitutionnel": "Analyse juridique",
    "Droit commercial": "Analyse juridique",
    "Introduction au droit": "Analyse juridique",
    "Introduction au droit administratif": "Analyse juridique",
    "Logique": "Raisonnement mathématique et modélisation",
    "R. I.": "Analyse juridique",
    # Électronique / systèmes
    "Electronique": "Électronique et systèmes embarqués",
    "Structure des Ordinateurs": "Électronique et systèmes embarqués",
    "Electricité": "Électronique et systèmes embarqués",
    "Télécom": "Électronique et systèmes embarqués",
    "NTT": "Création et production multimédia",
    "PAO": "Création et production multimédia",
    "Son": "Création et production multimédia",
    # Mécanique / industrie
    "Mécanique Générale": "Mécanique et technologies industrielles",
    "Mécanique Rationnelle": "Mécanique et technologies industrielles",
    "FM": "Mécanique et technologies industrielles",
    "OM": "Mécanique et technologies industrielles",
    "RDM": "Mécanique et technologies industrielles",
    "MCI": "Mécanique et technologies industrielles",
    "Mécanique des fluides": "Mécanique et technologies industrielles",
    "AUTOCAD": "Dessin technique et conception assistée",
    "Dessin": "Dessin technique et conception assistée",
    # Génie civil
    "MDC": "Génie civil et construction",
    "Géologie Appliquée": "Génie civil et construction",
    "Technologie des bâtiments": "Génie civil et construction",
    "Métré": "Génie civil et construction",
    "Hydraulique": "Génie civil et construction",
    "Topographie": "Génie civil et construction",
    "TP Topographie": "Génie civil et construction",
    # Chimie / mines
    "Chimie Minérale": "Chimie et sciences des matériaux",
    "Chimie Organique": "Chimie et sciences des matériaux",
    "Atomistique": "Chimie et sciences des matériaux",
    "Mines": "Géologie et exploitation minière",
    "Géodynamique Minière": "Géologie et exploitation minière",
    # Sciences du vivant
    "Génétique": "Biologie et sciences du vivant",
    "Biochimie": "Biologie et sciences du vivant",
    "Microbiologie": "Biologie et sciences du vivant",
    "Biologie Cellulaire": "Biologie et sciences du vivant",
    "Physiologie Animale": "Biologie et sciences du vivant",
    "Physiologie Végétale": "Biologie et sciences du vivant",
    "Biologie Végétale": "Biologie et sciences du vivant",
    "Biologie animale": "Biologie et sciences du vivant",
    # Tourisme / hôtellerie
    "Environnement": "Gestion environnementale et écotourisme",
    "Sites touristiques": "Gestion environnementale et écotourisme",
    "Ecologie Animale": "Gestion environnementale et écotourisme",
    "Flore": "Gestion environnementale et écotourisme",
    "Hygiène": "Hôtellerie, restauration et accueil",
    "Nutrition humaine": "Hôtellerie, restauration et accueil",
    "Art Culinaire": "Hôtellerie, restauration et accueil",
    "Science des aliments": "Hôtellerie, restauration et accueil",
}


def derive_competences(matieres: tuple[str, ...]) -> list[str]:
    """Renvoie les familles de compétences, dédupliquées et triées, couvertes
    par une liste de matières. Une matière absente du mapping est ignorée
    (elle reste visible dans la liste des matières, jamais perdue) plutôt que
    de provoquer une erreur — nouvelle matière scrapée un jour, ce script ne
    doit pas planter dessus.
    """
    familles = {
        MATIERE_TO_COMPETENCE[m] for m in matieres if m in MATIERE_TO_COMPETENCE
    }
    return sorted(familles)


def main() -> None:
    lines = [
        "# Compétences déduites par filière (première année)",
        "",
        "> **Ceci n'est PAS une donnée officielle de l'ISPM.** Le site officiel "
        "ne publie aucune liste de compétences distincte des matières "
        "(vérifié le 27/08/2026 sur ispm-edu.com/filieres.php et "
        "/presentation.php). Les compétences ci-dessous sont une inférence de "
        "l'équipe ORIENT'IA, dérivée mécaniquement des matières scrapées "
        "(SRC004) via une table matière→famille documentée dans "
        "`data_processing/derive_competences.py`. À présenter à l'utilisateur "
        "comme une estimation, jamais comme un fait officiel ISPM.",
        "",
    ]
    for code, filiere in FILIERES.items():
        competences = derive_competences(filiere.matieres)
        lines.append(f"## {filiere.nom} ({code})")
        lines.append("")
        lines.append("**Compétences déduites (non officielles) :**")
        lines.append("")
        for c in competences:
            lines.append(f"- {c}")
        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Dérivation terminée. Résultats dans {OUTPUT_MD}")


if __name__ == "__main__":
    main()
