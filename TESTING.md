# Tester ORIENT'IA — Machine Learning

Quatre niveaux de test, du plus automatique au plus proche de
l'utilisateur final.

## 1. Évaluation automatique complète (recommandé en premier)

```bash
python -m ml.train
```

Régénère les données synthétiques, ré-entraîne les 3 modèles (baseline
centroïde, k-NN, régression softmax), les compare sur un split de
validation, puis teste la généralisation sur l'enquête réelle
(`ORIENT'IA — Réponses.xlsx`). Écrit :

- `ml/artifacts/evaluation_report.md` — à lire en premier : comparaison
  des modèles, matrice de confusion, calibration, biais par série de bac,
  exemples d'erreurs, généralisation sur l'enquête.
- `ml/artifacts/evaluation_results.json` — même contenu en JSON.
- `data/ml/survey/registre_collecte.md` — traçabilité de l'enquête.

C'est l'équivalent du "jeu de test" du brief (sections 13/14) pour la
partie ML : pas d'accuracy seule, plusieurs métriques, erreurs et biais
documentés.

## 2. Tester le modèle seul, sans clé API

```bash
python -m ml.try_model
```

REPL en ligne de commande : tu tapes un profil (matières préférées,
compétences, centres d'intérêt — listes séparées par des virgules), il
affiche le classement des domaines d'orientation, leur score, les
filières ISPM correspondantes (lookup) et les "points forts" identifiés.
Ne nécessite ni `GEMINI_API_KEY` ni le reste de l'application — utile pour
vérifier rapidement que le modèle réagit sensément à un profil donné.

Exemple :
```
Matières préférées : Mathématiques, Informatique
Compétences déclarées : Analyse de données
Centres d'intérêt : Intelligence artificielle
```
→ classe en tête "Data Science, Statistique & Intelligence Artificielle"
(filières ISPM : ISAIA, IGGLIA).

## 3. Tester les outils de l'agent en isolation (sans LLM)

```bash
python -c "
from llm.tools import analyser_profil_ml, calculer_score_adequation, identifier_points_forts
print(analyser_profil_ml(matieres_preferees=['Droit'], centres_interet=['Justice']))
print(calculer_score_adequation('droit', matieres_preferees=['Droit']))
print(identifier_points_forts(centres_interet=['Droit']))
"
```

Vérifie que le pont entre `llm/tools.py` et `ml/inference.py` fonctionne,
sans dépendre du LLM ni d'une clé API.

## 4. Test de bout en bout, via l'agent conversationnel

Nécessite `GEMINI_API_KEY` dans `.env` (voir `.env.example`).

```bash
python -m llm.demo_cli
```

Pose une vraie question d'orientation (ex: « J'aime les maths et la
programmation, quel parcours me correspond ? ») et vérifie que l'agent :
- appelle bien `analyser_profil_ml` (visible dans les "Steps" affichés),
- cite les filières ISPM avec les sources documentaires (RAG),
- distingue explicitement le résultat du modèle ML des informations
  documentaires et de son propre texte (brief section 8).

L'API HTTP (`uvicorn api.main:app --reload`) et le frontend (`client/`)
passent par le même agent — les tester revient à tester le même chemin.

## Limites à garder en tête pendant les tests

- Le modèle est entraîné sur des données **synthétiques** ; sa
  performance en validation synthétique (~93% accuracy) mesure surtout sa
  capacité à retrouver les règles du générateur, pas sa validité sur une
  vraie population — voir la section "Généralisation" du rapport
  d'évaluation pour le test honnête sur l'enquête réelle (actuellement
  seulement 6 réponses).
- Le modèle ne doit jamais recevoir de trait de personnalité/caractère
  comme entrée — ce n'est pas un bug si `identifier_points_forts` ignore
  un champ "caractère" : c'est voulu (brief section 16).
