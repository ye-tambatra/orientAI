"""
Tools the conversational AI can call.

Each tool is a plain Python function with type hints and a docstring — the
google-genai SDK reads these to auto-generate the function-calling schema, so
no manual JSON schema is needed. Add new tools by writing a function here and
appending it to TOOLS.
"""

import datetime

from ml.inference import ModelNotTrainedError, get_model
from ml.vocab import SERIES_BAC
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
    matiere_preferee: str = "",
    environnement_prefere: str = "",
    motivation_principale: str = "",
    competence_principale: str = "",
    serie_bac: str = "",
) -> str:
    """Classe un profil candidat parmi les domaines généraux d'orientation
    pédagogique (Informatique, Data/IA, Commerce, Droit, Santé...) à l'aide
    du modèle de Machine Learning entraîné (régression softmax, ml/train.py).

    CRITIQUE : N'appelle JAMAIS ce tool directement si tu n'as pas d'abord
    collecté au moins la matière préférée, l'environnement de travail
    préféré ET la motivation principale (idéalement aussi la série de bac
    et une compétence). S'il te manque ne serait-ce qu'une de ces
    informations, tu DOIS d'abord appeler le tool
    `demarrer_questionnaire_orientation` pour la/les demander via
    l'interface. N'appelle ce tool qu'après que l'utilisateur ait soumis le
    questionnaire ou s'il a déjà fourni explicitement ces informations dans
    son message.

    Ces 5 champs correspondent exactement aux variables utilisées pour
    entraîner le modèle (voir ml/features.py) : matière/motivation/
    compétence sont converties en signaux de domaine, l'environnement et
    la série de bac sont des dimensions à part entière du vecteur de
    features. Ne saute pas la série de bac et la compétence par facilité :
    le modèle les utilise réellement et elles affinent nettement le score.

    Le modèle raisonne au niveau du DOMAINE d'orientation, pas directement
    au niveau d'une filière ISPM précise (un profil "j'aime l'IA et la
    programmation" ne permet pas encore de trancher entre IGGLIA, ISAIA,
    IMTICIA ou ESIIA — c'est un détail d'organisation interne de l'ISPM).
    Le résultat inclut donc, pour chaque domaine, les filières ISPM
    correspondantes à titre indicatif (table de correspondance fixe, PAS
    une prédiction du modèle) : vérifie leurs détails via les outils
    documentaires avant de recommander l'une d'elles précisément. Le
    résultat est une sortie STATISTIQUE du modèle : présente-la comme
    telle, distincte des informations documentaires (RAG) et de tes
    propres explications.

    Args:
        matiere_preferee: La matière préférée au lycée (ex: Mathématiques,
            Physique-Chimie, SVT, Français).
        environnement_prefere: L'environnement de travail préféré (ex:
            Bureau, Atelier/Terrain, Laboratoire, Contact clientèle,
            Télétravail).
        motivation_principale: Ce qui motive le plus l'utilisateur (ex: La
            technologie, Aider les autres, L'art et la création, Les
            affaires) — traité comme un centre d'intérêt.
        competence_principale: La compétence que l'utilisateur déclare
            comme la sienne (ex: Programmation, Analyse de données,
            Communication, Gestion de projet). Laisser vide si non précisé.
        serie_bac: La série de bac de l'utilisateur si connue (ex: S, D, C,
            A, L, Technique). Laisser vide si non précisé.
    """
    try:
        model = get_model()
    except ModelNotTrainedError as e:
        return _profil_ml_indisponible(str(e))

    profile = {
        "matieres_preferees": [matiere_preferee] if matiere_preferee else [],
        "competences": [competence_principale] if competence_principale else [],
        "centres_interet": [motivation_principale] if motivation_principale else [],
        "environnement_travail": environnement_prefere,
        "serie_bac": serie_bac,
    }
    ranking = model.rank_domaines(profile, k=3)
    if not ranking:
        return (
            "[Résultat du modèle ML] Aucune information exploitable dans le "
            "profil fourni : appelle demarrer_questionnaire_orientation pour "
            "recueillir la matière préférée, l'environnement de travail et "
            "la motivation principale avant de recommander une orientation."
        )
    lines = [
        f"{i + 1}. {r['label']} — filières ISPM à explorer : "
        f"{', '.join(r['filieres_ispm_correspondantes'])} (raison : {r['raison']})"
        for i, r in enumerate(ranking)
    ]
    confiance = ranking[0]["confiance"]
    confiance_phrase = {
        "nette": "Le premier domaine se détache clairement des autres.",
        "moderee": "Le premier domaine ressort, mais d'autres restent proches — ça vaut le coup de les garder en tête.",
        "incertaine": "Les domaines ci-dessous sont proches les uns des autres pour l'instant : pas assez d'éléments déclarés pour trancher nettement, il vaut mieux explorer plusieurs pistes plutôt que se fixer sur une seule.",
    }[confiance]
    return (
        "[Résultat du modèle ML ORIENT'IA — classement statistique par "
        "domaine d'orientation, pas une décision officielle. NE MENTIONNE "
        "AUCUN score numérique à l'utilisateur : reformule uniquement à "
        "partir du label du domaine, de la raison donnée et du niveau de "
        "confiance] D'après le profil déclaré, les domaines les plus "
        "compatibles sont :\n" +
        "\n".join(lines) +
        f"\n\nNiveau de confiance du classement : {confiance}. {confiance_phrase}" +
        "\nCette raison reflète uniquement les matières/compétences/intérêts "
        "explicitement déclarés par l'utilisateur — jamais un trait de "
        "personnalité ni une caractéristique personnelle sensible. Les "
        "filières ISPM listées sont une correspondance indicative, pas une "
        "sortie du modèle : vérifie leurs prérequis et débouchés réels via "
        "les outils documentaires avant de conclure."
    )


# Option lists sourced from ml.vocab so the questionnaire and the model's
# actual vocabulary can never silently drift apart (this already caught a
# real bug once: "Autre" was missing here even though it's a valid
# ml.vocab.SERIES_BAC value).
_ENVIRONNEMENT_OPTION_LABELS = {
    "bureau": "Bureau",
    "atelier": "Atelier",
    "laboratoire": "Laboratoire",
    "terrain": "Terrain / Plein air",
    "contact_client": "Contact clientèle",
}

# Wording adapts to who is answering (brief section 5 already distinguishes
# lycéens/étudiants from professionnels for the same reason): a bac-holder
# or a professional shouldn't be asked about their series "au lycée" in the
# present/future tense as if they hadn't chosen it yet.
_STATUTS = ("lyceen", "etudiant", "professionnel")

_MATIERE_LABELS = {
    "lyceen": "Quelle est votre matière préférée au lycée ?",
    "etudiant": "Quelle matière avez-vous préférée pendant vos études ?",
    "professionnel": "Quelle matière avez-vous préférée durant votre scolarité ?",
}
_SERIE_BAC_LABELS = {
    "lyceen": "Quelle série de bac avez-vous choisie (ou envisagez-vous de choisir) ?",
    "etudiant": "Quelle série de bac avez-vous obtenue ?",
    "professionnel": "Quelle série de bac aviez-vous obtenue ?",
}
_ENVIRONNEMENT_LABELS = {
    "lyceen": "Plus tard, dans quel type d'environnement aimerais-tu travailler ?",
    "etudiant": "Dans quel type d'environnement aimeriez-vous travailler ?",
    "professionnel": "Quel type d'environnement de travail préférez-vous ?",
}
_COMPETENCE_LABELS = {
    "lyceen": "Quelle compétence penses-tu développer le plus facilement ?",
    "etudiant": "Quelle compétence avez-vous le plus développée jusqu'ici ?",
    "professionnel": "Quelle est votre compétence la plus forte aujourd'hui ?",
}
# "Gestion de projet" présuppose une expérience professionnelle qu'un
# lycéen n'a généralement pas encore — remplacée par une option plus
# accessible pour ce statut.
_COMPETENCE_OPTIONS = {
    "lyceen": ["Programmation", "Analyse de données", "Communication", "Créativité", "Travail en équipe"],
    "etudiant": ["Programmation", "Analyse de données", "Communication", "Gestion de projet", "Créativité"],
    "professionnel": ["Programmation", "Analyse de données", "Communication", "Gestion de projet", "Créativité"],
}


def demarrer_questionnaire_orientation(
    matiere_preferee: str = "",
    environnement_prefere: str = "",
    motivation_principale: str = "",
    competence_principale: str = "",
    serie_bac: str = "",
    statut: str = "lyceen",
) -> str:
    """Déclenche l'affichage d'un questionnaire interactif sur l'interface utilisateur pour recueillir ses préférences.

    Utilise OBLIGATOIREMENT ceci quand l'utilisateur demande une recommandation de filière ou d'orientation et qu'il manque au moins une des 5 informations (matière, environnement, motivation, compétence, série de bac).
    Ces 5 champs correspondent exactement aux variables du modèle ML (voir analyser_profil_ml) : ne raccourcis pas le questionnaire à 3 questions, la série de bac et la compétence comptent réellement dans le score.
    Si l'utilisateur a déjà mentionné certaines de ses préférences dans son message,
    remplis les arguments correspondants pour que le questionnaire saute ces questions.

    Args:
        matiere_preferee: La matière préférée au lycée si l'utilisateur l'a mentionnée (ex: Mathématiques, Physique-Chimie, SVT, Français).
        environnement_prefere: L'environnement de travail préféré (ex: Bureau, Atelier, Laboratoire, Terrain, Contact clientèle).
        motivation_principale: Ce qui motive le plus l'utilisateur (ex: La technologie, Aider les autres, L'art et la création, Les affaires).
        competence_principale: La compétence que l'utilisateur reconnaît comme la sienne (ex: Programmation, Analyse de données, Communication).
        serie_bac: La série de bac (choisie ou envisagée) si l'utilisateur l'a mentionnée (ex: S, D, C, A, L, Technique).
        statut: Le statut de l'utilisateur si connu — "lyceen" (encore au
            lycée ou vient de passer le bac), "etudiant" (déjà dans
            l'enseignement supérieur) ou "professionnel" (déjà en activité,
            envisage une reconversion). Adapte le libellé des questions
            (temps des verbes, pertinence des options) : ne demande pas à
            un professionnel sa "matière préférée au lycée" au présent, et
            n'attends pas d'un lycéen qu'il ait une "compétence en gestion
            de projet". Par défaut "lyceen" (public majoritaire d'ORIENT'IA)
            si le statut n'a pas été précisé par l'utilisateur.
    """
    import json

    statut = statut if statut in _STATUTS else "lyceen"

    questions = []
    if not matiere_preferee:
        questions.append({
            "id": "matiere_preferee",
            "label": _MATIERE_LABELS[statut],
            "options": ["Mathématiques", "Physique-Chimie", "SVT", "Français", "Anglais"]
        })
    if not environnement_prefere:
        questions.append({
            "id": "environnement_prefere",
            "label": _ENVIRONNEMENT_LABELS[statut],
            "options": list(_ENVIRONNEMENT_OPTION_LABELS.values())
        })
    if not motivation_principale:
        questions.append({
            "id": "motivation_principale",
            "label": "Qu'est-ce qui vous motive le plus ?",
            "options": ["La technologie", "Aider les autres", "L'art et la création", "Les affaires"]
        })
    if not competence_principale:
        questions.append({
            "id": "competence_principale",
            "label": _COMPETENCE_LABELS[statut],
            "options": _COMPETENCE_OPTIONS[statut]
        })
    if not serie_bac:
        questions.append({
            "id": "serie_bac",
            "label": _SERIE_BAC_LABELS[statut],
            "options": list(SERIES_BAC)
        })

    return json.dumps({
        "action": "open_survey",
        "prefilled": {
            "matiere_preferee": matiere_preferee,
            "environnement_prefere": environnement_prefere,
            "motivation_principale": motivation_principale,
            "competence_principale": competence_principale,
            "serie_bac": serie_bac,
        },
        "questions": questions,
        "labels": {
            "matiere_preferee": "Matière préférée",
            "environnement_prefere": "Environnement de travail",
            "motivation_principale": "Motivation principale",
            "competence_principale": "Compétence principale",
            "serie_bac": "Série de bac",
        }
    })


def obtenir_informations_ispm() -> str:
    """Récupère les informations générales, les contacts et l'adresse de l'ISPM.

    Utilise ceci quand l'utilisateur demande où se trouve l'ISPM, comment
    les contacter (téléphone, email), ou des informations générales sur
    l'institut (historique court, localisation).
    """
    query = "Informations générales sur l'ISPM, contact, adresse, téléphone, email"
    return retrieve_context(query, n_results=4)


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
        f"[Résultat du modèle ML ORIENT'IA — NE MENTIONNE AUCUN score "
        f"numérique à l'utilisateur, reformule avec le niveau de confiance "
        f"et la raison] Adéquation avec le domaine « {result['label']} » : "
        f"confiance {result['confiance']} (ce domaine se classe "
        f"{result['rang_parmi_domaines']}e sur {result['nb_domaines']} pour "
        f"ce profil), raison : {result['raison']}. Filières ISPM "
        f"correspondantes à explorer : "
        f"{', '.join(result['filieres_ispm_correspondantes'])}. C'est une "
        "estimation statistique, pas une garantie de réussite ni une "
        "décision d'admission."
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
    """Explique pourquoi le modèle ML recommande un domaine donné : le poids
    RELATIF de chaque élément déclaré (matière, intérêt, compétence, série
    de bac, environnement) dans ce score, du plus au moins déterminant.

    Utilise ceci en priorité quand l'utilisateur demande explicitement
    "pourquoi" le modèle recommande un parcours/domaine — c'est plus
    précis que identifier_points_forts (qui ne donne que des labels). Le
    poids exact appris par le modèle n'est PAS destiné à être cité comme un
    chiffre à l'utilisateur (ex: "poids de 1.53") : reformule toujours en
    langage courant ("c'est surtout... qui joue en ta faveur", "... pèse
    peu ici") à partir du classement fort/modéré/faible fourni.

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
    max_positive = max((c["contribution"] for c in explanation["contributions"] if c["contribution"] > 0), default=0.0)

    def _qualitative(contribution: float) -> str:
        if contribution <= 0:
            return "joue en défaveur de ce domaine"
        if max_positive and contribution >= 0.66 * max_positive:
            return "pèse fortement en faveur de ce domaine"
        if max_positive and contribution >= 0.33 * max_positive:
            return "pèse modérément en faveur de ce domaine"
        return "pèse un peu en faveur de ce domaine"

    lines = [f"- {c['label']} : {_qualitative(c['contribution'])}" for c in explanation["contributions"]]
    return (
        f"[Résultat du modèle ML ORIENT'IA — NE MENTIONNE AUCUN chiffre "
        f"(ni score, ni poids) à l'utilisateur : reformule uniquement à "
        f"partir des qualificatifs fort/modéré/faible ci-dessous] Pour le "
        f"domaine « {explanation['label']} », voici les éléments déclarés "
        "par l'utilisateur qui expliquent ce résultat, du plus au moins "
        "déterminant :\n" + "\n".join(lines) +
        "\nSeuls les éléments explicitement déclarés par l'utilisateur "
        "apparaissent ici — jamais un trait de personnalité inféré."
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
    obtenir_informations_ispm,
    demarrer_questionnaire_orientation,
]
