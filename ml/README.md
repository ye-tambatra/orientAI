# ORIENT'IA — Machine Learning (Phase 2 du sujet)

Ce dossier implémente la composante Machine Learning d'ORIENT'IA : un
classifieur qui, à partir d'un profil (matières préférées, compétences,
centres d'intérêt, série de bac, environnement de travail souhaité), classe
les **domaines généraux d'orientation pédagogique et professionnelle**
(Informatique & Numérique, Data/IA, Commerce, Droit, Santé...) — pas
directement les 16 filières ISPM.

## Pourquoi un domaine général plutôt qu'une filière ISPM ?

Le rôle du Machine Learning ici est d'aider à répondre à « quel domaine
d'études/de métier correspond à ce profil ? » — une question d'orientation
pédagogique générale, indépendante d'un établissement précis. Un profil du
type « j'aime l'intelligence artificielle et la programmation » ne permet
pas raisonnablement de trancher entre IGGLIA, ISAIA, IMTICIA ou ESIIA :
cette distinction est un détail d'organisation interne du cursus ISPM, pas
quelque chose qu'un lycéen peut ou doit arbitrer à ce stade.

Le modèle prédit donc un **domaine** (`ml/domaines.py`, 15 domaines), et
chaque domaine porte une table de correspondance *fixe* (pas prédite) vers
ses filières ISPM plausibles. L'agent conversationnel affiche les deux :
le domaine (sortie du modèle) et les filières ISPM correspondantes (simple
lookup), puis s'appuie sur le RAG pour les détails réels de chaque filière
(prérequis, débouchés...).

## Pourquoi pas scikit-learn/pandas ?

Cet environnement n'a pas d'accès réseau fiable à PyPI pour les gros wheels
binaires (`scipy`, `pandas` ont systématiquement échoué au téléchargement).
`numpy` était déjà une dépendance du projet (via `chromadb`) ; tout le
pipeline ML est donc écrit en **numpy + stdlib pur** :
- `ml/xlsx_reader.py` relit le classeur d'enquête sans `openpyxl` (zip + XML).
- `ml/models.py` réimplémente 3 classifieurs (centroïde, k-NN, régression
  softmax) sans `scikit-learn`.

Résultat : zéro nouvelle dépendance dans `requirements.txt`, pipeline
100% reproductible hors-ligne, et chaque ligne de l'algorithme
d'apprentissage est auditable. Si le réseau devient fiable, migrer vers
scikit-learn est possible sans changer l'API (`fit`/`predict_proba`).

## Lancer le pipeline

```bash
python -m ml.synthetic   # régénère data/ml/synthetic/ seul (optionnel : train le fait déjà)
python -m ml.train       # génère les données, entraîne, évalue, écrit les artifacts
```

`ml/train.py` régénère à chaque exécution :
- `data/ml/synthetic/profils_synthetiques.csv` + `generation_doc.md`
- `data/ml/survey/reponses_anonymisees.csv` + `registre_collecte.md`
- `ml/artifacts/model.json` (modèle sélectionné, chargé par l'agent)
- `ml/artifacts/evaluation_results.json` + `evaluation_report.md`

Le notebook `ml/notebooks/01_eda_et_entrainement.ipynb` rejoue la même
démarche cellule par cellule (EDA, comparaison des 3 approches, matrice de
confusion, généralisation).

## Structure

| Fichier | Rôle |
|---|---|
| `domaines.py` | Les 15 domaines d'orientation (label space du modèle) + lookup vers les filières ISPM |
| `filieres.py` | Métadonnées des 16 filières ISPM (matières, mots-clés — source du lookup ci-dessus et réutilisable par le RAG/les outils) |
| `vocab.py` | Vocabulaire canonique (24 tags) + normalisation de texte libre, pondéré par domaine |
| `xlsx_reader.py` | Lecteur .xlsx sans dépendance |
| `synthetic.py` | Générateur de profils synthétiques, documenté (méthode/hypothèses/biais) |
| `survey.py` | Chargement de l'enquête réelle + registre de collecte |
| `features.py` | Profil (dict) → vecteur numérique |
| `models.py` | 3 classifieurs numpy (baseline, k-NN, softmax) |
| `metrics.py` | Accuracy, top-k, macro-F1, matrice de confusion, MRR, calibration, stabilité |
| `train.py` | Orchestration : entraînement + évaluation + écriture des artifacts |
| `inference.py` | `OrientationModel`, utilisé par `llm/tools.py` |

## Comment le modèle est intégré à l'agent (section 8 du sujet)

`llm/tools.py` expose trois outils réels (pas des instructions de prompt) :
`analyser_profil_ml`, `calculer_score_adequation`, `identifier_points_forts`.
Chacun appelle `ml.inference.get_model()` et préfixe sa réponse par
`[Résultat du modèle ML ORIENT'IA]` pour que l'agent distingue explicitement
la sortie du modèle statistique (le domaine) de la correspondance ISPM
(un lookup fixe, pas une prédiction), des informations documentaires (RAG)
et de son propre texte généré (voir `SYSTEM_INSTRUCTION` dans `llm/agent.py`).

Le modèle n'utilise **jamais** de trait de personnalité, de caractéristique
personnelle sensible ni d'inférence psychologique — seulement ce que
l'utilisateur déclare explicitement comme matières/compétences/intérêts
(conformité section 16 du sujet).

## Limites à connaître (voir le rapport complet pour le détail)

- Les données d'entraînement sont synthétiques : les affinités
  matière/domaine sont une hypothèse de conception, pas une statistique
  observée (documenté dans `data/ml/synthetic/generation_doc.md`).
- L'enquête réelle ne compte, à ce stade, que 6 réponses — toutes de la
  population étudiante/lycéenne, aucune du côté professionnels. Le test de
  généralisation sur cette enquête (`ml/artifacts/evaluation_report.md`)
  est donc un indicateur de cohérence, pas une preuve statistique. À
  recalculer une fois l'enquête plus fournie.
- Le modèle prédit un domaine d'orientation, jamais un débouché ni un
  prérequis d'une filière ISPM précise : ces faits doivent venir du RAG
  (`rag/retriever.py`), jamais du modèle ML ni du LLM seul.
- La correspondance domaine → filière(s) ISPM (`ml.domaines`) est une
  table hand-curated, pas apprise ; elle mérite d'être relue par quelqu'un
  qui connaît finement l'offre ISPM actuelle avant la démonstration finale.
