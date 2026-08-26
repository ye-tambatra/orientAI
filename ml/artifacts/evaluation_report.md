# Rapport d'évaluation — Machine Learning ORIENT'IA

Généré par `python -m ml.train`. Le modèle classe un profil parmi 15 **domaines d'orientation pédagogique généraux** (`ml.domaines`), pas directement parmi les filières ISPM — voir `ml/domaines.py` pour la justification. Montage : entraînement sur données synthétiques, validation sur un split synthétique tenu à part, test de généralisation sur les réponses réelles de l'enquête (voir `data/ml/survey/registre_collecte.md`).

- Profils d'entraînement (synthétiques) : 1800
- Profils de validation (synthétiques, tenus à part) : 450
- **Meilleur modèle sur cette validation (macro-F1) : `baseline_centroide`**
- **Modèle réellement déployé dans le chat : `softmax_regression`**

> Ces deux lignes diffèrent volontairement cette fois-ci : `baseline_centroide` gagne sur la métrique brute, mais `softmax_regression` reste déployé car c'est le seul des 3 modèles dont les poids sont interprétables par variable (nécessaire pour `expliquer_recommandation_ml`, qui répond à la question de démonstration "Pourquoi ton modèle recommande-t-il ce parcours ?"). `NearestCentroidBaseline` et `KNNClassifier` n'ont pas de poids par variable et ne peuvent pas fournir cette explication — voir `ml/train.py` pour le détail.

## Comparaison des approches (validation synthétique)

| Modèle | Accuracy | Top-3 accuracy | Macro-F1 | MRR | Stabilité |
|---|---|---|---|---|---|
| baseline_centroide | 0.902 | 0.971 | 0.903 | 0.939 | 0.984 |
| knn | 0.900 | 0.951 | 0.900 | 0.930 | 0.973 |
| softmax_regression | 0.902 | 0.976 | 0.903 | 0.940 | 0.983 |

`baseline_centroide` est le modèle de référence simple exigé par le brief (section 7). `stabilité` = fraction des profils dont le top-1 ne change pas sous une petite perturbation gaussienne du vecteur de traits (voir `ml.metrics.stability_score`).

## Détail du modèle déployé (`softmax_regression`)

### Rapport par domaine (precision / recall / F1 / support)

| Domaine | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| agriculture_elevage — Agriculture & Élevage | 0.87 | 1.00 | 0.93 | 26 |
| agroalimentaire — Agroalimentaire | 0.97 | 0.85 | 0.91 | 34 |
| chimie_mines — Chimie, Mines & Industries Pétrolières | 0.97 | 0.83 | 0.89 | 35 |
| commerce_gestion — Commerce, Marketing & Gestion des Affaires | 0.93 | 0.90 | 0.92 | 31 |
| data_ia — Data Science, Statistique & Intelligence Artificielle | 0.85 | 0.92 | 0.88 | 36 |
| droit — Droit & Techniques Juridiques | 0.90 | 0.96 | 0.93 | 28 |
| economie_management — Économie & Management de Projet | 0.81 | 0.76 | 0.79 | 29 |
| finance_comptabilite — Finance & Comptabilité | 0.76 | 0.79 | 0.77 | 28 |
| genie_civil — Génie Civil & Architecture | 0.86 | 0.97 | 0.91 | 32 |
| genie_industriel — Génie Industriel, Mécanique & Électrotechnique | 0.94 | 0.94 | 0.94 | 33 |
| hotellerie_restauration — Hôtellerie & Restauration | 0.93 | 1.00 | 0.96 | 27 |
| informatique_numerique — Informatique & Numérique (développement, gestion, multimédia) | 0.96 | 0.79 | 0.87 | 33 |
| pharmacie_sante — Pharmacie & Santé | 0.92 | 0.88 | 0.90 | 25 |
| reseaux_electronique — Réseaux, Électronique & Systèmes | 0.94 | 1.00 | 0.97 | 34 |
| tourisme_environnement — Tourisme & Environnement | 0.95 | 1.00 | 0.97 | 19 |

### Table de calibration (confiance du top-1 vs exactitude empirique)

| Intervalle de confiance | n | Confiance moyenne | Exactitude empirique |
|---|---|---|---|
| [0.0, 0.3) | 3 | 0.27 | 0.33 |
| [0.3, 0.5) | 20 | 0.41 | 0.55 |
| [0.5, 0.7) | 47 | 0.61 | 0.72 |
| [0.7, 0.9) | 224 | 0.83 | 0.93 |
| [0.9, 1.0] | 156 | 0.93 | 0.97 |

### Matrice de confusion (lignes = vrai, colonnes = prédit)

| | agriculture_elevage | agroalimentaire | chimie_mines | commerce_gestion | data_ia | droit | economie_management | finance_comptabilite | genie_civil | genie_industriel | hotellerie_restauration | informatique_numerique | pharmacie_sante | reseaux_electronique | tourisme_environnement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **agriculture_elevage** | 26 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **agroalimentaire** | 2 | 29 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| **chimie_mines** | 0 | 0 | 29 | 0 | 1 | 0 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 1 | 0 |
| **commerce_gestion** | 0 | 0 | 0 | 28 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| **data_ia** | 0 | 0 | 0 | 0 | 33 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 0 | 0 |
| **droit** | 0 | 0 | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| **economie_management** | 0 | 0 | 0 | 1 | 0 | 3 | 22 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **finance_comptabilite** | 0 | 0 | 0 | 1 | 1 | 0 | 4 | 22 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **genie_civil** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 31 | 0 | 0 | 0 | 0 | 0 | 0 |
| **genie_industriel** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 31 | 0 | 0 | 0 | 0 | 0 |
| **hotellerie_restauration** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 0 |
| **informatique_numerique** | 0 | 0 | 0 | 0 | 4 | 0 | 1 | 0 | 1 | 0 | 0 | 26 | 0 | 1 | 0 |
| **pharmacie_sante** | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 22 | 0 | 0 |
| **reseaux_electronique** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 34 | 0 |
| **tourisme_environnement** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 19 |

### Analyse d'erreurs (exemples de validation mal classés)

- Matières = « Mathématiques, Gestion / Entreprise, Mathématiques », intérêts = « Gestion / Entreprise » → vrai **finance_comptabilite**, prédit **economie_management**
- Matières = « Langues étrangères, Mathématiques, Statistiques / Données », intérêts = « Langues étrangères, Gestion / Entreprise » → vrai **economie_management**, prédit **finance_comptabilite**
- Matières = « Statistiques / Données, Economie, Statistiques / Données, Intelligence artificielle », intérêts = « Statistiques / Données, Intelligence artificielle, Mathématiques » → vrai **chimie_mines**, prédit **data_ia** *(étiquette bruitée par construction)*
- Matières = « Intelligence artificielle, Informatique / Programmation », intérêts = « Intelligence artificielle » → vrai **informatique_numerique**, prédit **data_ia**
- Matières = « Statistiques / Données, Statistiques / Données, Statistiques / Données, Finance / Comptabilité », intérêts = « Mathématiques » → vrai **genie_industriel**, prédit **finance_comptabilite** *(étiquette bruitée par construction)*
- Matières = « Droit / Juridique, Langues étrangères », intérêts = « Droit / Juridique » → vrai **economie_management**, prédit **droit** *(étiquette bruitée par construction)*
- Matières = « Multimédia / Design numérique, Informatique / Programmation », intérêts = « Informatique / Programmation, Multimédia / Design numérique » → vrai **data_ia**, prédit **informatique_numerique** *(étiquette bruitée par construction)*
- Matières = « Mathématiques, Langues étrangères », intérêts = « Statistiques / Données » → vrai **finance_comptabilite**, prédit **economie_management**

### Étude de biais

Aucun attribut démographique (genre, âge, origine) n'est utilisé par le modèle — choix de conception, pas absence de signal disponible (brief section 16). Le seul attribut de profil scolaire disponible, la série du baccalauréat, sert de sous-groupe pour vérifier que l'exactitude du modèle ne s'effondre pas sur un sous-groupe particulier :

| Série bac | Exactitude (sous-groupe) |
|---|---|
| D | 0.89 |
| A | 0.92 |
| S | 0.93 |
| Autre | 0.90 |
| Technique | 0.64 |
| L | 0.94 |
| C | 0.91 |

## Généralisation : évaluation sur l'enquête réelle

- Réponses d'enquête utilisables : **6**
- Top-1 prédit ∈ domaines candidats du répondant : **83%**
- Top-3 prédit ∩ domaines candidats ≠ ∅ : **100%**

> **Limite majeure à ne pas masquer** : cet échantillon ne compte que 6 réponses, toutes de la population étudiante/lycéenne (aucun professionnel à ce jour), et le « domaine candidat » est lui-même déduit du texte libre du répondant par correspondance de mots-clés — voir `ml.survey.map_to_candidate_domaines`. Ce chiffre est un indicateur de cohérence grossier, pas une estimation fiable du taux de généralisation réel. Il devra être recalculé à mesure que l'enquête collecte davantage de réponses (idéalement avant le gel de fin de première journée prévu par le brief).

| Répondant | Population | Parcours déclaré | Domaines candidats | Top-3 prédit | Filières ISPM (top-1) | Top-1 ok | Top-3 ok |
|---|---|---|---|---|---|---|---|
| R001 | etudiant_lyceen | Intelligence Artificielle | data_ia, informatique_numerique, reseaux_electronique | data_ia, reseaux_electronique, informatique_numerique | ISAIA, IGGLIA | ✅ | ✅ |
| R002 | etudiant_lyceen | Intelligence Artificielle | data_ia, informatique_numerique, reseaux_electronique | data_ia, reseaux_electronique, genie_industriel | ISAIA, IGGLIA | ✅ | ✅ |
| R003 | etudiant_lyceen | Informatique / Technologies de l’Information et de la Communication | informatique_numerique, data_ia, reseaux_electronique | informatique_numerique, data_ia, reseaux_electronique | IGGLIA, IMTICIA | ✅ | ✅ |
| R004 | etudiant_lyceen | Informatique / Technologies de l’Information et de la Communication | informatique_numerique, data_ia, reseaux_electronique | informatique_numerique, data_ia, reseaux_electronique | IGGLIA, IMTICIA | ✅ | ✅ |
| R005 | etudiant_lyceen | Informatique / Technologies de l’Information et de la Communication | informatique_numerique, data_ia, reseaux_electronique | commerce_gestion, hotellerie_restauration, informatique_numerique | CAA | ❌ | ✅ |
| R006 | etudiant_lyceen | Informatique / Technologies de l’Information et de la Communication | informatique_numerique, data_ia, reseaux_electronique | data_ia, reseaux_electronique, informatique_numerique | ISAIA, IGGLIA | ✅ | ✅ |

## Limites générales du jeu de données et du modèle

- Les profils synthétiques encodent des hypothèses de conception (affinités matière/domaine choisies à la main) — voir `data/ml/synthetic/generation_doc.md`. Une performance élevée en validation synthétique mesure surtout la capacité du modèle à retrouver ces règles, pas sa validité sur une population réelle — d'où le test de généralisation ci-dessus.
- Le trait de personnalité auto-déclaré (« caractère ») collecté par l'enquête n'est jamais utilisé comme variable d'entrée, conformément à l'interdiction de profilage psychologique du brief.
- Le modèle prédit un **domaine d'orientation général**, pas directement une filière ISPM : la correspondance domaine → filière(s) ISPM (`ml.domaines.DOMAINES[...].ispm_filieres`) est une table de correspondance fixe, pas une prédiction du modèle. Ni le modèle ni le LLM n'inventent de débouché, de prérequis ou de modalité d'admission : ces faits doivent venir du RAG (`rag/retriever.py`).
