# Registre de collecte — enquête ORIENT'IA

Ce registre documente l'enquête réelle utilisée comme jeu de validation/test du modèle de Machine Learning (brief section 5, "Traçabilité de la collecte"). Il est généré à partir du fichier source `ORIENT'IA — Réponses.xlsx` (export Google Forms/Sheets) — voir `ml/survey.py:write_registre`.

## Le questionnaire (version effectivement diffusée)

Extrait des en-têtes de colonnes du formulaire réellement soumis (texte exact des questions) :

- J'accepte que mes réponses anonymisées soient utilisées dans le cadre du projet ORIENT'IA.
- Quel est votre statut actuel ?
- Quel est votre niveau actuel au lycée ?
- Quelle série avez-vous choisie (ou envisagez-vous de choisir) au bac ?
- Quelle(s) matière(s) préférez-vous ?
- Quel est votre parcours actuel ?
- Comment décririez-vous votre caractère ?
- Quels sont vos principaux centres d'intérêt ?
- Êtes-vous satisfait(e) de votre parcours ?
- Le métier que vous visez correspond-il à votre parcours actuel ?
- Quel parcours de formation avez-vous suivi ?
- Votre travail actuel correspond-il à ce parcours ?
- Quels sont vos principaux centres d'intérêt professionnels ?
- Avec le recul, êtes-vous satisfait(e) de ce parcours ?
- Avez-vous une remarque ou un conseil concernant l'orientation scolaire et professionnelle ?

URL publique du formulaire : https://docs.google.com/forms/d/e/1FAIpQLSd1asKpUKZaOuLHrPUN5db6Q8ismS7gclEh36yZ4HPA7Nzh0A/viewform

## Populations visées et mode de diffusion

Deux populations complémentaires, comme demandé par le brief :
- **Étudiants/lycéens** — profil actuel, parcours actuellement suivi ou envisagé.
- **Professionnels** — profil avant leurs études, parcours suivi, adéquation jugée rétrospectivement.

Mode de diffusion propre à chaque population : **[À COMPLÉTER PAR L'ÉQUIPE]** — ce fichier n'enregistre que les réponses elles-mêmes, pas le canal par lequel le lien du formulaire a circulé (réseaux sociaux, diffusion directe, affichage, etc.). Ne pas laisser ce champ vide dans la version remise au jury.

## Période de collecte et volumétrie

- Période observée dans cet export : 2026-08-26 15:18:55 → 2026-08-26 15:34:33
- Réponses reçues (lignes de l'export) : 6
- Réponses retenues pour l'entraînement/l'évaluation : 6
- Réponses écartées : 0

### Répartition des réponses retenues

- etudiant_lyceen : 6

**Limite à nommer explicitement** : à la date de cet export, l'échantillon (6 réponses) est trop restreint pour toute conclusion statistique et ne contient, pour l'instant, aucune réponse de la population « professionnels ». Les intervalles de confiance sur les métriques calculées à partir de cet échantillon sont donc très larges et doivent être présentés comme tels — voir ml/artifacts/evaluation_report.md.

## Texte de consentement présenté aux répondants

> J'accepte que mes réponses anonymisées soient utilisées dans le cadre du projet ORIENT'IA.

Seules les réponses affirmatives ("Oui, j'accepte de participer") sont chargées par `ml.survey.load_survey` ; les autres sont exclues avec le motif `consentement absent`.

## Procédure d'anonymisation

Le formulaire ne demande explicitement ni nom, ni numéro de téléphone, ni adresse e-mail (anonymisation par construction, documentée dans l'onglet README du classeur source). Aucun traitement de dé-identification supplémentaire n'a donc été nécessaire côté pipeline.

## Traitements postérieurs appliqués et justification

- Les questions dépendant de la population (parcours actuel vs parcours suivi, centres d'intérêt "étudiant" vs "professionnel") sont fusionnées dans un schéma de profil unique (`ml.features`) selon la colonne « statut actuel ».
- Le champ « caractère » (trait de personnalité auto-déclaré) est conservé dans cet export brut mais **n'est jamais utilisé comme variable du modèle** — conformément à l'interdiction du brief (section 16) de fonder une recommandation sur un profil psychologique.
- Le parcours déclaré en texte libre est rattaché à un ensemble de domaines d'orientation *candidats* (ml.domaines) par correspondance de mots-clés (`ml.survey.map_to_candidate_domaines`), plutôt qu'à un domaine unique, car les répondants ne sont pas nécessairement des étudiants ISPM et décrivent un champ d'études en langage libre. Les réponses sans correspondance sont écartées (motif : « parcours déclaré non rattachable à un domaine d'orientation ») et comptabilisées ci-dessus.

## Biais d'échantillonnage constatés

- Auto-sélection : à ce stade, 100% des réponses proviennent de la population étudiante/lycéenne, et une forte proportion déclare un intérêt pour l'intelligence artificielle — cohérent avec une diffusion initiale dans l'entourage immédiat de l'équipe projet plutôt que dans un échantillon représentatif.
- Aucune réponse « professionnel » ne permet, pour l'instant, de mesurer l'adéquation rétrospective parcours/métier que le brief identifie comme la population la plus informative.
