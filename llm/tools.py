"""
Tools the conversational AI can call.

Each tool is a plain Python function with type hints and a docstring — the
google-genai SDK reads these to auto-generate the function-calling schema, so
no manual JSON schema is needed. Add new tools by writing a function here and
appending it to TOOLS.
"""

import datetime

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

def verifier_prerequis(filiere: str = "", serie_bac: str = "") -> str:
    """Vérifie les conditions d'admission/prérequis, documents à fournir et séries de baccalauréat.

    Utilise ceci quand l'utilisateur demande s'il peut intégrer l'ISPM,
    quels documents ou séries de baccalauréat sont requis.

    Args:
        filiere: Le nom ou sigle de la filière concernée (ex: ISAIA, IMTICIA). Laisser vide si non précisée.
        serie_bac: La série du baccalauréat de l'utilisateur, si connue
            (ex: C, D, S). Laisser vide si non précisée.
    """
    query = "Conditions d'accès, d'admission et prérequis en première année"
    return retrieve_context(query, n_results=4)

def comparer_parcours(filiere_a: str, filiere_b: str) -> str:
    """Compare deux filières/parcours de l'ISPM entre elles.

    Utilise ceci quand l'utilisateur hésite entre deux filières et veut les
    comparer.

    Args:
        filiere_a: Le nom ou sigle de la première filière.
        filiere_b: Le nom ou sigle de la deuxième filière.
    """
    contexte_a = retrieve_context(
        f"Présentation et parcours de la filière {filiere_a}", n_results=10
    )
    contexte_b = retrieve_context(
        f"Présentation et parcours de la filière {filiere_b}", n_results=10
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
    return retrieve_context(query, n_results=15)

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

def analyser_profil_ml(interets: list[str], points_forts: list[str] | None = None) -> str:
    """Analyse le profil complet d'un utilisateur pour suggérer des filières adaptées.

    CRITIQUE : N'appelle JAMAIS ce tool directement si tu n'as pas d'abord collecté les 3 informations requises : la matière préférée, l'environnement de travail préféré ET la motivation principale. 
    S'il te manque ne serait-ce qu'une de ces 3 informations, tu DOIS d'abord appeler le tool `demarrer_questionnaire_orientation` pour la/les demander via l'interface. 
    N'appelle ce tool qu'après que l'utilisateur ait soumis le questionnaire ou s'il a déjà fourni explicitement ces 3 informations dans son message.

    Args:
        interets: Les matières ou domaines qui intéressent l'utilisateur (inclure la matière, l'environnement et la motivation collectés).
        points_forts: Les points forts/compétences de l'utilisateur, si connus.
    """
    # TODO: integrate the ML
    interets_str = ", ".join(interets) if interets else "non précisés"
    return (
        f"Sur la base de votre profil (intérêts : {interets_str}), "
        "le modèle d'orientation vous recommande la filière IMTICIA (Ingénierie de Management, d'Informatique et d'Intelligence Artificielle). "
        "C'est une filière excellente pour ceux qui aiment la technologie et souhaitent travailler dans ce domaine."
    )

def demarrer_questionnaire_orientation(
    matiere_preferee: str = "",
    environnement_prefere: str = "",
    motivation_principale: str = ""
) -> str:
    """Déclenche l'affichage d'un questionnaire interactif sur l'interface utilisateur pour recueillir ses préférences.
    
    Utilise OBLIGATOIREMENT ceci quand l'utilisateur demande une recommandation de filière ou d'orientation et qu'il manque au moins une des 3 informations (matière, environnement, motivation).
    Si l'utilisateur a déjà mentionné certaines de ses préférences dans son message, 
    remplis les arguments correspondants pour que le questionnaire saute ces questions.
    
    Args:
        matiere_preferee: La matière préférée au lycée si l'utilisateur l'a mentionnée (ex: Mathématiques, Physique-Chimie, SVT, Français).
        environnement_prefere: L'environnement de travail préféré (ex: Bureau, Plein air, Laboratoire, Télétravail).
        motivation_principale: Ce qui motive le plus l'utilisateur (ex: La technologie, Aider les autres, L'art et la création, Les affaires).
    """
    import json
    
    questions = []
    if not matiere_preferee:
        questions.append({
            "id": "matiere_preferee",
            "label": "Quelle est votre matière préférée au lycée ?",
            "options": ["Mathématiques", "Physique-Chimie", "SVT", "Français", "Anglais"]
        })
    if not environnement_prefere:
        questions.append({
            "id": "environnement_prefere",
            "label": "Quel type d'environnement de travail préférez-vous ?",
            "options": ["Bureau", "Plein air", "Laboratoire", "Télétravail"]
        })
    if not motivation_principale:
        questions.append({
            "id": "motivation_principale",
            "label": "Qu'est-ce qui vous motive le plus ?",
            "options": ["La technologie", "Aider les autres", "L'art et la création", "Les affaires"]
        })

    return json.dumps({
        "action": "open_survey",
        "prefilled": {
            "matiere_preferee": matiere_preferee,
            "environnement_prefere": environnement_prefere,
            "motivation_principale": motivation_principale
        },
        "questions": questions,
        "labels": {
            "matiere_preferee": "Matière préférée",
            "environnement_prefere": "Environnement de travail",
            "motivation_principale": "Motivation principale"
        }
    })

def calculer_score_adequation(filiere: str, interets: list[str] | None = None) -> str:
    """Calcule un score d'adéquation entre un utilisateur et une filière.

    Attention : ce calcul n'est pas encore implémenté. Si ce tool est appelé,
    informe l'utilisateur honnêtement que cette fonctionnalité n'est pas
    encore disponible plutôt que d'inventer un score.

    Args:
        filiere: Le nom ou sigle de la filière concernée.
        interets: Les matières ou domaines qui intéressent l'utilisateur.
    """
    return (
        "Le calcul de score d'adéquation avec une filière n'est pas encore "
        "disponible."
    )

def obtenir_informations_ispm() -> str:
    """Récupère les informations générales, les contacts et l'adresse de l'ISPM.

    Utilise ceci quand l'utilisateur demande où se trouve l'ISPM, comment
    les contacter (téléphone, email), ou des informations générales sur
    l'institut (historique court, localisation).
    """
    query = "Informations générales sur l'ISPM, contact, adresse, téléphone, email"
    return retrieve_context(query, n_results=4)


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
    expliquer_recommandation,
    obtenir_informations_ispm,
    demarrer_questionnaire_orientation,
]
