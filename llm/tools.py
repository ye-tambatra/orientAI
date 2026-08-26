"""
Tools the conversational AI can call.

Each tool is a plain Python function with type hints and a docstring — the
google-genai SDK reads these to auto-generate the function-calling schema, so
no manual JSON schema is needed. Add new tools by writing a function here and
appending it to TOOLS.
"""

import datetime

from ml.inference import ModelNotTrainedError, get_model
from rag.retriever import retrieve_context


def get_current_time() -> str:
    """Retourne la date et l'heure actuelles.

    Utilise ceci quand l'utilisateur demande la date, le jour ou l'heure
    actuelle.
    """
    return datetime.datetime.now().isoformat()


def echo(text: str) -> str:
    """Répète le texte donné mot pour mot.

    Utilise ceci uniquement quand l'utilisateur te demande explicitement de
    répéter quelque chose.
    """
    return text


def rechercher_formation(mot_cle: str) -> str:
    """Recherche les filières/formations de l'ISPM en rapport avec un mot-clé.

    Utilise ceci quand l'utilisateur demande quelles filières existent, ce
    qu'est une filière donnée, ou cherche une formation sur un thème
    (ex: informatique, agriculture, gestion).

    Args:
        mot_cle: Le thème, domaine ou nom de filière recherché.
    """
    query = f"Filière ou formation en rapport avec {mot_cle} à l'ISPM"
    return retrieve_context(query, n_results=4)


def verifier_prerequis(filiere: str, serie_bac: str = "") -> str:
    """Vérifie les conditions d'admission/prérequis pour une filière donnée.

    Utilise ceci quand l'utilisateur demande s'il peut intégrer une filière,
    quels documents ou séries de baccalauréat sont requis.

    Args:
        filiere: Le nom ou sigle de la filière concernée (ex: ISAIA, IMTICIA).
        serie_bac: La série du baccalauréat de l'utilisateur, si connue
            (ex: C, D, S). Laisser vide si non précisée.
    """
    query = f"Conditions d'admission et prérequis pour la filière {filiere}"
    if serie_bac:
        query += f" pour un baccalauréat série {serie_bac}"
    return retrieve_context(query, n_results=3)


def comparer_parcours(filiere_a: str, filiere_b: str) -> str:
    """Compare deux filières/parcours de l'ISPM entre elles.

    Utilise ceci quand l'utilisateur hésite entre deux filières et veut les
    comparer.

    Args:
        filiere_a: Le nom ou sigle de la première filière.
        filiere_b: Le nom ou sigle de la deuxième filière.
    """
    contexte_a = retrieve_context(
        f"Présentation et parcours de la filière {filiere_a}", n_results=3
    )
    contexte_b = retrieve_context(
        f"Présentation et parcours de la filière {filiere_b}", n_results=3
    )
    return (
        f"== {filiere_a} ==\n{contexte_a}\n\n"
        f"== {filiere_b} ==\n{contexte_b}"
    )


def rechercher_competences(filiere: str) -> str:
    """Recherche les matières/compétences enseignées en première année d'une filière.

    Utilise ceci quand l'utilisateur demande ce qu'on apprend/étudie dans une
    filière donnée.

    Args:
        filiere: Le nom ou sigle de la filière concernée.
    """
    query = (
        f"Liste des matières et compétences enseignées en première année "
        f"de la filière {filiere}"
    )
    return retrieve_context(query, n_results=3)


def expliquer_recommandation(filiere: str, raison: str = "") -> str:
    """Rassemble les informations pour justifier pourquoi une filière peut convenir.

    Utilise ceci après avoir identifié une filière potentiellement adaptée à
    l'utilisateur, pour retrouver les faits (présentation, compétences,
    objectifs) qui justifient la recommandation. Compose ensuite ta propre
    explication à partir de ces faits.

    Args:
        filiere: Le nom ou sigle de la filière recommandée.
        raison: Le critère de l'utilisateur à mettre en avant si connu
            (ex: intérêt pour la biologie). Laisser vide si non précisé.
    """
    query = f"Pourquoi choisir la filière {filiere} : présentation, compétences et objectifs"
    if raison:
        query += f", en lien avec {raison}"
    return retrieve_context(query, n_results=4)


def identifier_debouches(filiere: str) -> str:
    """Cherche les débouchés professionnels/perspectives de carrière d'une filière.

    Attention : cette information n'est pas encore disponible dans la base de
    connaissances. Si ce tool est appelé, informe l'utilisateur honnêtement
    que cette information n'est pas encore disponible plutôt que d'inventer
    une réponse.

    Args:
        filiere: Le nom ou sigle de la filière concernée.
    """
    return (
        "Les débouchés professionnels ne sont pas encore renseignés dans la "
        f"base de connaissances pour la filière {filiere}."
    )


def _profil_ml_indisponible(detail: str) -> str:
    return (
        "[Modèle ML indisponible] Le modèle de Machine Learning d'ORIENT'IA "
        f"n'a pas pu être chargé ({detail}). Informe l'utilisateur "
        "honnêtement que cette analyse statistique n'est pas disponible "
        "plutôt que d'inventer un résultat."
    )


def analyser_profil_ml(
    matieres_preferees: list[str] | None = None,
    competences: list[str] | None = None,
    centres_interet: list[str] | None = None,
    serie_bac: str = "",
    environnement_travail: str = "",
) -> str:
    """Classe un profil candidat parmi les domaines généraux d'orientation
    pédagogique (Informatique, Data/IA, Commerce, Droit, Santé...) à l'aide
    du modèle de Machine Learning entraîné (régression softmax, ml/train.py).

    Le modèle raisonne au niveau du DOMAINE d'orientation, pas directement
    au niveau d'une filière ISPM précise (un profil "j'aime l'IA et la
    programmation" ne permet pas encore de trancher entre IGGLIA, ISAIA,
    IMTICIA ou ESIIA — c'est un détail d'organisation interne de l'ISPM).
    Le résultat inclut donc, pour chaque domaine, les filières ISPM
    correspondantes à titre indicatif (table de correspondance fixe, PAS
    une prédiction du modèle) : vérifie leurs détails via les outils
    documentaires avant de recommander l'une d'elles précisément.

    Utilise ceci dès que tu as recueilli au moins un élément de profil
    (matières préférées, compétences ou centres d'intérêt) et que
    l'utilisateur souhaite une recommandation d'orientation. Le résultat
    est une sortie STATISTIQUE du modèle : présente-la comme telle,
    distincte des informations documentaires (RAG) et de tes propres
    explications. Combine-la ensuite avec les outils documentaires
    (rechercher_formation, verifier_prerequis, identifier_debouches...)
    pour justifier et sourcer la recommandation finale — ne présente
    jamais le score seul comme une décision d'admission.

    Args:
        matieres_preferees: Les matières que l'utilisateur préfère.
        competences: Les compétences déclarées par l'utilisateur.
        centres_interet: Les centres d'intérêt déclarés par l'utilisateur.
        serie_bac: La série de bac de l'utilisateur si connue (ex: S, D, C,
            A, L, Technique). Signal utile — un lycéen en filière littéraire
            (L) n'a par exemple statistiquement pas le même profil qu'un
            candidat en série scientifique. Laisser vide si non précisé, et
            demander l'info à l'utilisateur si elle n'a pas encore été donnée.
        environnement_travail: Le type d'environnement de travail recherché
            si connu (ex: bureau, atelier, laboratoire, terrain,
            contact_client). Laisser vide si non précisé.
    """
    try:
        model = get_model()
    except ModelNotTrainedError as e:
        return _profil_ml_indisponible(str(e))

    profile = {
        "matieres_preferees": matieres_preferees or [],
        "competences": competences or [],
        "centres_interet": centres_interet or [],
        "serie_bac": serie_bac,
        "environnement_travail": environnement_travail,
    }
    ranking = model.rank_domaines(profile, k=3)
    if not ranking:
        return (
            "[Résultat du modèle ML] Aucune information exploitable dans le "
            "profil fourni : pose des questions pour recueillir des "
            "matières, compétences ou centres d'intérêt avant de "
            "recommander une orientation."
        )
    lines = [
        f"{i + 1}. {r['label']} (score du modèle : {r['score']:.2f}) — "
        f"filières ISPM à explorer : {', '.join(r['filieres_ispm_correspondantes'])}"
        for i, r in enumerate(ranking)
    ]
    return (
        "[Résultat du modèle ML ORIENT'IA — classement statistique par "
        "domaine d'orientation, pas une décision officielle] D'après le "
        "profil déclaré, les domaines les plus compatibles sont :\n" +
        "\n".join(lines) +
        "\nCe score reflète uniquement les matières/compétences/intérêts "
        "explicitement déclarés par l'utilisateur — il n'utilise ni trait de "
        "personnalité, ni caractéristique personnelle sensible. Les "
        "filières ISPM listées sont une correspondance indicative, pas une "
        "sortie du modèle : vérifie leurs prérequis et débouchés réels via "
        "les outils documentaires avant de conclure."
    )


def calculer_score_adequation(
    domaine: str,
    matieres_preferees: list[str] | None = None,
    competences: list[str] | None = None,
    centres_interet: list[str] | None = None,
    serie_bac: str = "",
    environnement_travail: str = "",
) -> str:
    """Calcule le score d'adéquation (modèle ML) entre un profil et UN domaine
    d'orientation donné (ex: "data_ia", "commerce_gestion", "droit"...).

    Utilise ceci quand l'utilisateur demande explicitement à quel point il
    correspond à un domaine précis (par opposition à analyser_profil_ml,
    qui classe tous les domaines entre eux).

    Args:
        domaine: L'identifiant du domaine d'orientation (voir la liste
            renvoyée par analyser_profil_ml, ex: "data_ia", "droit",
            "commerce_gestion", "genie_civil"...).
        matieres_preferees: Les matières que l'utilisateur préfère.
        competences: Les compétences déclarées par l'utilisateur.
        centres_interet: Les centres d'intérêt déclarés par l'utilisateur.
        serie_bac: La série de bac de l'utilisateur si connue (ex: S, D, C,
            A, L, Technique). Laisser vide si non précisé.
        environnement_travail: Le type d'environnement de travail recherché
            si connu (ex: bureau, atelier, laboratoire, terrain,
            contact_client). Laisser vide si non précisé.
    """
    try:
        model = get_model()
    except ModelNotTrainedError as e:
        return _profil_ml_indisponible(str(e))

    profile = {
        "matieres_preferees": matieres_preferees or [],
        "competences": competences or [],
        "centres_interet": centres_interet or [],
        "serie_bac": serie_bac,
        "environnement_travail": environnement_travail,
    }
    result = model.score_adequation(profile, domaine)
    if "error" in result:
        return f"[Modèle ML] {result['error']}"
    return (
        f"[Résultat du modèle ML ORIENT'IA] Score d'adéquation pour le "
        f"domaine « {result['label']} » : {result['score']:.2f} (sur une "
        f"échelle de probabilité 0-1 ; ce domaine se classe "
        f"{result['rang_parmi_domaines']}e/{result['nb_domaines']} pour ce "
        f"profil). Filières ISPM correspondantes à explorer : "
        f"{', '.join(result['filieres_ispm_correspondantes'])}. Ce chiffre "
        "est une estimation statistique, pas une garantie de réussite ni "
        "une décision d'admission."
    )


def identifier_points_forts(
    matieres_preferees: list[str] | None = None,
    competences: list[str] | None = None,
    centres_interet: list[str] | None = None,
) -> str:
    """Identifie, parmi les éléments DÉCLARÉS par l'utilisateur, ceux qui pèsent
    le plus dans la recommandation du modèle ML.

    N'utilise que les matières/compétences/centres d'intérêt explicitement
    donnés par l'utilisateur — n'infère jamais un trait de personnalité ou
    un point fort à partir du style d'écriture ou du ton des messages.

    Args:
        matieres_preferees: Les matières que l'utilisateur préfère.
        competences: Les compétences déclarées par l'utilisateur.
        centres_interet: Les centres d'intérêt déclarés par l'utilisateur.
    """
    try:
        model = get_model()
    except ModelNotTrainedError as e:
        return _profil_ml_indisponible(str(e))

    profile = {
        "matieres_preferees": matieres_preferees or [],
        "competences": competences or [],
        "centres_interet": centres_interet or [],
    }
    points = model.points_forts(profile)
    if not points:
        return (
            "[Modèle ML] Pas assez d'éléments déclarés pour identifier des "
            "points forts. Demande à l'utilisateur ses matières préférées, "
            "compétences ou centres d'intérêt."
        )
    return (
        "[Résultat du modèle ML ORIENT'IA] Éléments déclarés par "
        "l'utilisateur qui pèsent le plus dans sa recommandation actuelle : "
        + ", ".join(points) + "."
    )


def expliquer_recommandation_ml(
    matieres_preferees: list[str] | None = None,
    competences: list[str] | None = None,
    centres_interet: list[str] | None = None,
    serie_bac: str = "",
    environnement_travail: str = "",
    domaine: str = "",
) -> str:
    """Explique QUANTITATIVEMENT pourquoi le modèle ML recommande un domaine
    donné : la contribution numérique exacte de chaque élément déclaré
    (matière, intérêt, compétence, série de bac, environnement) au score
    de ce domaine, triée par importance.

    Utilise ceci en priorité quand l'utilisateur demande explicitement
    "pourquoi" le modèle recommande un parcours/domaine — c'est plus
    précis que identifier_points_forts (qui ne donne que des labels) : ici
    tu obtiens de vrais chiffres tracés jusqu'aux poids appris par le
    modèle, à citer tels quels plutôt qu'à reformuler de façon vague.

    Args:
        matieres_preferees: Les matières que l'utilisateur préfère.
        competences: Les compétences déclarées par l'utilisateur.
        centres_interet: Les centres d'intérêt déclarés par l'utilisateur.
        serie_bac: La série de bac si connue.
        environnement_travail: L'environnement de travail souhaité si connu.
        domaine: L'identifiant du domaine à expliquer (ex: "data_ia"). Si
            vide, explique le domaine que le modèle recommande en premier
            pour ce profil.
    """
    try:
        model = get_model()
    except ModelNotTrainedError as e:
        return _profil_ml_indisponible(str(e))

    profile = {
        "matieres_preferees": matieres_preferees or [],
        "competences": competences or [],
        "centres_interet": centres_interet or [],
        "serie_bac": serie_bac,
        "environnement_travail": environnement_travail,
    }
    explanation = model.expliquer_recommandation(profile, domaine_id=domaine or None)
    if not explanation["contributions"]:
        return (
            "[Modèle ML] Pas assez d'éléments déclarés dans le profil pour "
            "expliquer une recommandation. Demande à l'utilisateur ses "
            "matières, compétences ou centres d'intérêt d'abord."
        )
    lines = [
        f"- {c['label']} : contribution {c['contribution']:+.2f} "
        f"(poids appris par le modèle : {c['poids_appris']:+.2f})"
        for c in explanation["contributions"]
    ]
    return (
        f"[Résultat du modèle ML ORIENT'IA] Pour le domaine « "
        f"{explanation['label']} » (score : {explanation['score']:.2f}), "
        "voici les éléments déclarés par l'utilisateur qui pèsent le plus "
        "dans ce score, du plus au moins déterminant :\n" + "\n".join(lines) +
        f"\n(biais de base du modèle pour ce domaine, indépendant du "
        f"profil : {explanation['biais_du_modele']:+.2f}). Une contribution "
        "positive pousse vers ce domaine, une contribution négative "
        "l'éloigne. Seuls les éléments explicitement déclarés par "
        "l'utilisateur apparaissent ici — jamais un trait de personnalité "
        "inféré."
    )


TOOLS = [
    get_current_time,
    echo,
    rechercher_formation,
    verifier_prerequis,
    comparer_parcours,
    rechercher_competences,
    analyser_profil_ml,
    identifier_debouches,
    calculer_score_adequation,
    identifier_points_forts,
    expliquer_recommandation_ml,
    expliquer_recommandation,
]
