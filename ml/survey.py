"""Loader for the real survey responses ("ORIENT'IA — Réponses.xlsx").

Implements the "Acquisition par enquête" requirement (brief section 5):
the form targets two populations sharing most questions but branching on
a few ("parcours actuel" for students vs "parcours suivi" for
professionals; "centres d'intérêt" vs "centres d'intérêt professionnels";
etc.). This module normalises both branches into the same profile schema
used everywhere else in ml/ (see ml.features), and maps the free-text
"parcours" answer to a *set* of plausible general orientation domains
(ml.domaines — see `map_to_candidate_domaines`) since respondents are not
restricted to ISPM and describe a field of study/work in their own words,
not an ISPM filière sigle (brief section 5: "sans restriction
d'établissement").

Nothing here invents facts about how the survey was diffused: fields the
team alone knows (diffusion channel per population, exclusion rationale)
are left as explicit placeholders in the generated register rather than
fabricated — see write_registre().
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from ml.domaines import DOMAINES
from ml.vocab import normalize_free_text
from ml.xlsx_reader import read_sheet

SHEET_NAME = "Form Responses 1"

COL_TIMESTAMP = "Timestamp"
COL_CONSENT = "J'accepte que mes réponses anonymisées soient utilisées dans le cadre du projet ORIENT'IA."
COL_STATUT = "Quel est votre statut actuel ?"
COL_NIVEAU = "Quel est votre niveau actuel au lycée ?"
COL_SERIE = "Quelle série avez-vous choisie (ou envisagez-vous de choisir) au bac ?"
COL_MATIERES = "Quelle(s) matière(s) préférez-vous ?"
COL_PARCOURS_ACTUEL = "Quel est votre parcours actuel ?"
COL_CARACTERE = "Comment décririez-vous votre caractère ?"
COL_INTERETS_ETUDIANT = "Quels sont vos principaux centres d'intérêt ?"
COL_SATISFACTION_ETUDIANT = "Êtes-vous satisfait(e) de votre parcours ?"
COL_METIER_CORRESPOND = "Le métier que vous visez correspond-il à votre parcours actuel ?"
COL_PARCOURS_SUIVI = "Quel parcours de formation avez-vous suivi ?"
COL_TRAVAIL_CORRESPOND = "Votre travail actuel correspond-il à ce parcours ?"
COL_INTERETS_PRO = "Quels sont vos principaux centres d'intérêt professionnels ?"
COL_SATISFACTION_PRO = "Avec le recul, êtes-vous satisfait(e) de ce parcours ?"
COL_REMARQUE = "Avez-vous une remarque ou un conseil concernant l'orientation scolaire et professionnelle ?"

STATUTS_ETUDIANT = {"Étudiant(e)", "Lycéen(ne)"}


def _excel_serial_to_iso(serial: str) -> str:
    try:
        dt = datetime(1899, 12, 30) + timedelta(days=float(serial))
        return dt.isoformat(sep=" ", timespec="seconds")
    except (ValueError, TypeError):
        return ""


def map_to_candidate_domaines(text: str, threshold: float = 0.5) -> list[str]:
    """Free-text 'parcours' answer -> plausible general orientation domains.

    A respondent (student or professional, "sans restriction
    d'établissement") describes their field in their own words, which
    rarely matches one of ml.domaines' labels exactly. We normalise the
    text to canonical tags (ml.vocab) and return every domain whose
    affinity with at least one of those tags is >= threshold, ranked by
    best affinity. Returns [] when nothing matches ("non classifiable" ->
    excluded from the evaluation set, logged in the collection register).
    """
    tags = normalize_free_text(text)
    if not tags:
        return []
    from ml.vocab import get_tag
    scores: dict[str, float] = {}
    for tag_id in tags:
        tag = get_tag(tag_id)
        for domaine_id, w in tag.weights.items():
            if w >= threshold:
                scores[domaine_id] = max(scores.get(domaine_id, 0.0), w)
    return sorted(scores, key=scores.get, reverse=True)


@dataclass
class SurveyRow:
    respondent_id: str
    population: str  # "etudiant_lyceen" | "professionnel" | "non_classifiable"
    profile: dict
    label_text: str
    candidate_domaines: list[str]
    satisfaction: float | None
    metier_correspond: str
    collected_at: str
    excluded_reason: str | None = None


def load_survey(path: str) -> list[SurveyRow]:
    raw_rows = read_sheet(path, SHEET_NAME)
    rows: list[SurveyRow] = []
    for i, r in enumerate(raw_rows):
        respondent_id = f"R{i + 1:03d}"
        consent = r.get(COL_CONSENT, "")
        collected_at = _excel_serial_to_iso(r.get(COL_TIMESTAMP, ""))
        if not consent.lower().startswith("oui"):
            rows.append(SurveyRow(respondent_id, "exclu", {}, "", [], None, "",
                                   collected_at, excluded_reason="consentement absent"))
            continue

        statut = r.get(COL_STATUT, "")
        if statut in STATUTS_ETUDIANT:
            profile = {
                "matieres_preferees": r.get(COL_MATIERES, ""),
                "centres_interet": r.get(COL_INTERETS_ETUDIANT, ""),
                "competences": "",  # not asked; see note below
                "environnement_travail": "",
                "serie_bac": r.get(COL_SERIE, ""),
            }
            label_text = r.get(COL_PARCOURS_ACTUEL, "")
            satisfaction_raw = r.get(COL_SATISFACTION_ETUDIANT, "")
            metier_correspond = r.get(COL_METIER_CORRESPOND, "")
            population = "etudiant_lyceen"
        elif "professionnel" in statut.lower():
            profile = {
                "matieres_preferees": "",
                "centres_interet": r.get(COL_INTERETS_PRO, ""),
                "competences": "",
                "environnement_travail": "",
                "serie_bac": "",
            }
            label_text = r.get(COL_PARCOURS_SUIVI, "")
            satisfaction_raw = r.get(COL_SATISFACTION_PRO, "")
            metier_correspond = r.get(COL_TRAVAIL_CORRESPOND, "")
            population = "professionnel"
        else:
            rows.append(SurveyRow(respondent_id, "non_classifiable", {}, "", [], None, "",
                                   collected_at, excluded_reason=f"statut inconnu: {statut!r}"))
            continue

        candidates = map_to_candidate_domaines(label_text)
        satisfaction = float(satisfaction_raw) if satisfaction_raw else None
        excluded_reason = None if candidates else "parcours déclaré non rattachable à un domaine d'orientation"

        rows.append(SurveyRow(
            respondent_id=respondent_id,
            population=population,
            profile=profile,
            label_text=label_text,
            candidate_domaines=candidates,
            satisfaction=satisfaction,
            metier_correspond=metier_correspond,
            collected_at=collected_at,
            excluded_reason=excluded_reason,
        ))
    return rows


def usable_rows(rows: list[SurveyRow]) -> list[SurveyRow]:
    """Rows with consent, a recognised population and >= 1 candidate
    domaine — i.e. usable for model validation/testing."""
    return [r for r in rows if r.excluded_reason is None and r.population in
            ("etudiant_lyceen", "professionnel")]


# --- exports -----------------------------------------------------------

QUESTIONNAIRE = [
    COL_CONSENT, COL_STATUT, COL_NIVEAU, COL_SERIE, COL_MATIERES,
    COL_PARCOURS_ACTUEL, COL_CARACTERE, COL_INTERETS_ETUDIANT,
    COL_SATISFACTION_ETUDIANT, COL_METIER_CORRESPOND, COL_PARCOURS_SUIVI,
    COL_TRAVAIL_CORRESPOND, COL_INTERETS_PRO, COL_SATISFACTION_PRO, COL_REMARQUE,
]


def write_anonymized_csv(rows: list[SurveyRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "respondent_id", "population", "collected_at", "matieres_preferees",
            "centres_interet", "serie_bac", "parcours_declare",
            "domaines_candidats", "satisfaction", "metier_correspond", "exclu_raison",
        ])
        for r in rows:
            writer.writerow([
                r.respondent_id, r.population, r.collected_at,
                r.profile.get("matieres_preferees", ""),
                r.profile.get("centres_interet", ""),
                r.profile.get("serie_bac", ""),
                r.label_text,
                "|".join(r.candidate_domaines),
                r.satisfaction if r.satisfaction is not None else "",
                r.metier_correspond,
                r.excluded_reason or "",
            ])


def write_registre(rows: list[SurveyRow], path: Path, source_file: str) -> None:
    total = len(rows)
    excluded = [r for r in rows if r.excluded_reason]
    kept = [r for r in rows if not r.excluded_reason]
    by_population: dict[str, int] = {}
    for r in kept:
        by_population[r.population] = by_population.get(r.population, 0) + 1
    dates = sorted(r.collected_at for r in rows if r.collected_at)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Registre de collecte — enquête ORIENT'IA\n\n")
        f.write(
            "Ce registre documente l'enquête réelle utilisée comme jeu de "
            "validation/test du modèle de Machine Learning (brief section 5, "
            "\"Traçabilité de la collecte\"). Il est généré à partir du fichier "
            f"source `{source_file}` (export Google Forms/Sheets) — voir "
            "`ml/survey.py:write_registre`.\n\n"
        )
        f.write("## Le questionnaire (version effectivement diffusée)\n\n")
        f.write(
            "Extrait des en-têtes de colonnes du formulaire réellement soumis "
            "(texte exact des questions) :\n\n"
        )
        for q in QUESTIONNAIRE:
            f.write(f"- {q}\n")
        f.write(
            "\nURL publique du formulaire : "
            "https://docs.google.com/forms/d/e/1FAIpQLSd1asKpUKZaOuLHrPUN5db6Q8ismS7gclEh36yZ4HPA7Nzh0A/viewform\n"
        )
        f.write(
            "\n## Populations visées et mode de diffusion\n\n"
            "Deux populations complémentaires, comme demandé par le brief :\n"
            "- **Étudiants/lycéens** — profil actuel, parcours actuellement suivi ou envisagé.\n"
            "- **Professionnels** — profil avant leurs études, parcours suivi, "
            "adéquation jugée rétrospectivement.\n\n"
            "Mode de diffusion propre à chaque population : "
            "**[À COMPLÉTER PAR L'ÉQUIPE]** — ce fichier n'enregistre que les "
            "réponses elles-mêmes, pas le canal par lequel le lien du "
            "formulaire a circulé (réseaux sociaux, diffusion directe, "
            "affichage, etc.). Ne pas laisser ce champ vide dans la version "
            "remise au jury.\n"
        )
        f.write(
            "\n## Période de collecte et volumétrie\n\n"
            f"- Période observée dans cet export : {dates[0] if dates else 'n/a'} "
            f"→ {dates[-1] if dates else 'n/a'}\n"
            f"- Réponses reçues (lignes de l'export) : {total}\n"
            f"- Réponses retenues pour l'entraînement/l'évaluation : {len(kept)}\n"
            f"- Réponses écartées : {len(excluded)}\n"
        )
        for r in excluded:
            f.write(f"  - {r.respondent_id} : {r.excluded_reason}\n")
        f.write("\n### Répartition des réponses retenues\n\n")
        for pop, n in by_population.items():
            f.write(f"- {pop} : {n}\n")
        f.write(
            "\n**Limite à nommer explicitement** : à la date de cet export, "
            f"l'échantillon ({len(kept)} réponses) est trop restreint pour "
            "toute conclusion statistique et ne contient, pour l'instant, "
            "aucune réponse de la population « professionnels ». Les "
            "intervalles de confiance sur les métriques calculées à partir de "
            "cet échantillon sont donc très larges et doivent être présentés "
            "comme tels — voir ml/artifacts/evaluation_report.md.\n"
        )
        f.write(
            "\n## Texte de consentement présenté aux répondants\n\n"
            f"> {COL_CONSENT}\n\n"
            "Seules les réponses affirmatives (\"Oui, j'accepte de participer\") "
            "sont chargées par `ml.survey.load_survey` ; les autres sont "
            "exclues avec le motif `consentement absent`.\n"
        )
        f.write(
            "\n## Procédure d'anonymisation\n\n"
            "Le formulaire ne demande explicitement ni nom, ni numéro de "
            "téléphone, ni adresse e-mail (anonymisation par construction, "
            "documentée dans l'onglet README du classeur source). Aucun "
            "traitement de dé-identification supplémentaire n'a donc été "
            "nécessaire côté pipeline.\n"
        )
        f.write(
            "\n## Traitements postérieurs appliqués et justification\n\n"
            "- Les questions dépendant de la population (parcours actuel vs "
            "parcours suivi, centres d'intérêt \"étudiant\" vs "
            "\"professionnel\") sont fusionnées dans un schéma de profil "
            "unique (`ml.features`) selon la colonne « statut actuel ».\n"
            "- Le champ « caractère » (trait de personnalité auto-déclaré) "
            "est conservé dans cet export brut mais **n'est jamais utilisé "
            "comme variable du modèle** — conformément à l'interdiction du "
            "brief (section 16) de fonder une recommandation sur un profil "
            "psychologique.\n"
            "- Le parcours déclaré en texte libre est rattaché à un ensemble "
            "de domaines d'orientation *candidats* (ml.domaines) par "
            "correspondance de mots-clés (`ml.survey.map_to_candidate_domaines`), "
            "plutôt qu'à un domaine unique, car les répondants ne sont pas "
            "nécessairement des étudiants ISPM et décrivent un champ "
            "d'études en langage libre. Les réponses sans correspondance "
            "sont écartées (motif : « parcours déclaré non rattachable à un "
            "domaine d'orientation ») et comptabilisées ci-dessus.\n"
        )
        f.write(
            "\n## Biais d'échantillonnage constatés\n\n"
            "- Auto-sélection : à ce stade, 100% des réponses proviennent de "
            "la population étudiante/lycéenne, et une forte proportion "
            "déclare un intérêt pour l'intelligence artificielle — cohérent "
            "avec une diffusion initiale dans l'entourage immédiat de "
            "l'équipe projet plutôt que dans un échantillon représentatif.\n"
            "- Aucune réponse « professionnel » ne permet, pour l'instant, de "
            "mesurer l'adéquation rétrospective parcours/métier que le brief "
            "identifie comme la population la plus informative.\n"
        )
