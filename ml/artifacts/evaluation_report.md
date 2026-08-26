# Rapport d'évaluation — Machine Learning ORIENT'IA

Généré par `python -m ml.train`. Le modèle classe un profil parmi 15 **domaines d'orientation pédagogique généraux** (`ml.domaines`), pas directement parmi les filières ISPM — voir `ml/domaines.py` pour la justification. Montage : entraînement sur données synthétiques, validation sur un split synthétique tenu à part, test de généralisation sur les réponses réelles de l'enquête (voir `data/ml/survey/registre_collecte.md`).

- Profils d'entraînement (synthétiques) : 1800
- Profils de validation (synthétiques, tenus à part) : 450
- **Modèle sélectionné (meilleur macro-F1 en validation) : `softmax_regression`**

## Comparaison des approches (validation synthétique)

| Modèle | Accuracy | Top-3 accuracy | Macro-F1 | MRR | Stabilité |
|---|---|---|---|---|---|
| baseline_centroide | 0.918 | 0.958 | 0.917 | 0.944 | 0.984 |
| knn | 0.913 | 0.949 | 0.913 | 0.936 | 0.983 |
| softmax_regression | 0.929 | 0.960 | 0.928 | 0.951 | 0.985 |

`baseline_centroide` est le modèle de référence simple exigé par le brief (section 7). `stabilité` = fraction des profils dont le top-1 ne change pas sous une petite perturbation gaussienne du vecteur de traits (voir `ml.metrics.stability_score`).

## Détail du modèle sélectionné (`softmax_regression`)

### Rapport par domaine (precision / recall / F1 / support)

| Domaine | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| agriculture_elevage — Agriculture & Élevage | 0.85 | 1.00 | 0.92 | 23 |
| agroalimentaire — Agroalimentaire | 0.97 | 0.97 | 0.97 | 34 |
| chimie_mines — Chimie, Mines & Industries Pétrolières | 0.91 | 0.83 | 0.87 | 24 |
| commerce_gestion — Commerce, Marketing & Gestion des Affaires | 0.97 | 0.91 | 0.94 | 34 |
| data_ia — Data Science, Statistique & Intelligence Artificielle | 0.94 | 0.86 | 0.90 | 35 |
| droit — Droit & Techniques Juridiques | 0.94 | 0.97 | 0.95 | 30 |
| economie_management — Économie & Management de Projet | 0.90 | 0.90 | 0.90 | 29 |
| finance_comptabilite — Finance & Comptabilité | 0.86 | 0.97 | 0.91 | 33 |
| genie_civil — Génie Civil & Architecture | 0.89 | 0.89 | 0.89 | 28 |
| genie_industriel — Génie Industriel, Mécanique & Électrotechnique | 0.91 | 0.97 | 0.94 | 32 |
| hotellerie_restauration — Hôtellerie & Restauration | 0.96 | 0.96 | 0.96 | 27 |
| informatique_numerique — Informatique & Numérique (développement, gestion, multimédia) | 0.97 | 0.86 | 0.91 | 35 |
| pharmacie_sante — Pharmacie & Santé | 1.00 | 0.89 | 0.94 | 36 |
| reseaux_electronique — Réseaux, Électronique & Systèmes | 0.93 | 1.00 | 0.96 | 26 |
| tourisme_environnement — Tourisme & Environnement | 0.92 | 1.00 | 0.96 | 24 |

### Table de calibration (confiance du top-1 vs exactitude empirique)

| Intervalle de confiance | n | Confiance moyenne | Exactitude empirique |
|---|---|---|---|
| [0.0, 0.3) | 2 | 0.27 | 0.50 |
| [0.3, 0.5) | 16 | 0.41 | 0.81 |
| [0.5, 0.7) | 54 | 0.61 | 0.89 |
| [0.7, 0.9) | 242 | 0.83 | 0.94 |
| [0.9, 1.0] | 136 | 0.93 | 0.95 |

### Matrice de confusion (lignes = vrai, colonnes = prédit)

| | agriculture_elevage | agroalimentaire | chimie_mines | commerce_gestion | data_ia | droit | economie_management | finance_comptabilite | genie_civil | genie_industriel | hotellerie_restauration | informatique_numerique | pharmacie_sante | reseaux_electronique | tourisme_environnement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **agriculture_elevage** | 23 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **agroalimentaire** | 0 | 33 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **chimie_mines** | 0 | 1 | 20 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| **commerce_gestion** | 0 | 0 | 0 | 31 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| **data_ia** | 0 | 0 | 0 | 0 | 30 | 0 | 1 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| **droit** | 0 | 0 | 0 | 0 | 0 | 29 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| **economie_management** | 0 | 0 | 0 | 0 | 0 | 1 | 26 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| **finance_comptabilite** | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **genie_civil** | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 25 | 1 | 0 | 0 | 0 | 0 | 0 |
| **genie_industriel** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 31 | 0 | 0 | 0 | 0 | 0 |
| **hotellerie_restauration** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 26 | 0 | 0 | 0 | 1 |
| **informatique_numerique** | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 2 | 0 | 0 | 0 | 30 | 0 | 1 | 0 |
| **pharmacie_sante** | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 32 | 0 | 0 |
| **reseaux_electronique** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 26 | 0 |
| **tourisme_environnement** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 24 |

### Analyse d'erreurs (exemples de validation mal classés)

- Matières = « Biologie / Santé, Agriculture / Elevage », intérêts = « Biologie / Santé, Agriculture / Elevage » → vrai **pharmacie_sante**, prédit **agriculture_elevage** *(étiquette bruitée par construction)*
- Matières = « Droit / Juridique, Langues étrangères », intérêts = « Droit / Juridique, Langues étrangères » → vrai **commerce_gestion**, prédit **droit** *(étiquette bruitée par construction)*
- Matières = « Mécanique / Industrie, Mines / Géologie, Mines / Géologie, Mécanique / Industrie », intérêts = « Chimie, Mines / Géologie, Chimie » → vrai **agroalimentaire**, prédit **chimie_mines** *(étiquette bruitée par construction)*
- Matières = « Tourisme / Environnement, Langues étrangères », intérêts = « Tourisme / Environnement, Langues étrangères » → vrai **economie_management**, prédit **tourisme_environnement** *(étiquette bruitée par construction)*
- Matières = « Mathématiques, Langues étrangères, Statistiques / Données », intérêts = « Mathématiques, Finance / Comptabilité » → vrai **data_ia**, prédit **finance_comptabilite** *(étiquette bruitée par construction)*
- Matières = « Langues étrangères, Tourisme / Environnement », intérêts = « Hôtellerie / Accueil » → vrai **hotellerie_restauration**, prédit **tourisme_environnement**
- Matières = « Biologie / Santé, Agriculture / Elevage », intérêts = « Agriculture / Elevage » → vrai **pharmacie_sante**, prédit **agriculture_elevage** *(étiquette bruitée par construction)*
- Matières = « Droit / Juridique, Langues étrangères », intérêts = « Droit / Juridique » → vrai **economie_management**, prédit **droit** *(étiquette bruitée par construction)*

### Étude de biais

Aucun attribut démographique (genre, âge, origine) n'est utilisé par le modèle — choix de conception, pas absence de signal disponible (brief section 16). Le seul attribut de profil scolaire disponible, la série du baccalauréat, sert de sous-groupe pour vérifier que l'exactitude du modèle ne s'effondre pas sur un sous-groupe particulier :

| Série bac | Exactitude (sous-groupe) |
|---|---|
| Autre | 0.93 |
| D | 0.91 |
| C | 0.89 |
| A | 0.89 |
| L | 0.94 |
| Technique | 0.92 |
| S | 0.98 |

## Généralisation : évaluation sur l'enquête réelle

- Réponses d'enquête utilisables : **6**
- Top-1 prédit ∈ domaines candidats du répondant : **83%**
- Top-3 prédit ∩ domaines candidats ≠ ∅ : **100%**

> **Limite majeure à ne pas masquer** : cet échantillon ne compte que 6 réponses, toutes de la population étudiante/lycéenne (aucun professionnel à ce jour), et le « domaine candidat » est lui-même déduit du texte libre du répondant par correspondance de mots-clés — voir `ml.survey.map_to_candidate_domaines`. Ce chiffre est un indicateur de cohérence grossier, pas une estimation fiable du taux de généralisation réel. Il devra être recalculé à mesure que l'enquête collecte davantage de réponses (idéalement avant le gel de fin de première journée prévu par le brief).

| Répondant | Population | Parcours déclaré | Domaines candidats | Top-3 prédit | Filières ISPM (top-1) | Top-1 ok | Top-3 ok |
|---|---|---|---|---|---|---|---|
| R001 | etudiant_lyceen | Intelligence Artificielle | data_ia, informatique_numerique, reseaux_electronique | data_ia, reseaux_electronique, informatique_numerique | ISAIA, IGGLIA | ✅ | ✅ |
| R002 | etudiant_lyceen | Intelligence Artificielle | data_ia, informatique_numerique, reseaux_electronique | data_ia, genie_industriel, reseaux_electronique | ISAIA, IGGLIA | ✅ | ✅ |
| R003 | etudiant_lyceen | Informatique / Technologies de l’Information et de la Communication | informatique_numerique, data_ia, reseaux_electronique | informatique_numerique, data_ia, reseaux_electronique | IGGLIA, IMTICIA | ✅ | ✅ |
| R004 | etudiant_lyceen | Informatique / Technologies de l’Information et de la Communication | informatique_numerique, data_ia, reseaux_electronique | informatique_numerique, data_ia, reseaux_electronique | IGGLIA, IMTICIA | ✅ | ✅ |
| R005 | etudiant_lyceen | Informatique / Technologies de l’Information et de la Communication | informatique_numerique, data_ia, reseaux_electronique | commerce_gestion, hotellerie_restauration, informatique_numerique | CAA | ❌ | ✅ |
| R006 | etudiant_lyceen | Informatique / Technologies de l’Information et de la Communication | informatique_numerique, data_ia, reseaux_electronique | data_ia, reseaux_electronique, informatique_numerique | ISAIA, IGGLIA | ✅ | ✅ |

## Limites générales du jeu de données et du modèle

- Les profils synthétiques encodent des hypothèses de conception (affinités matière/domaine choisies à la main) — voir `data/ml/synthetic/generation_doc.md`. Une performance élevée en validation synthétique mesure surtout la capacité du modèle à retrouver ces règles, pas sa validité sur une population réelle — d'où le test de généralisation ci-dessus.
- Le trait de personnalité auto-déclaré (« caractère ») collecté par l'enquête n'est jamais utilisé comme variable d'entrée, conformément à l'interdiction de profilage psychologique du brief.
- Le modèle prédit un **domaine d'orientation général**, pas directement une filière ISPM : la correspondance domaine → filière(s) ISPM (`ml.domaines.DOMAINES[...].ispm_filieres`) est une table de correspondance fixe, pas une prédiction du modèle. Ni le modèle ni le LLM n'inventent de débouché, de prérequis ou de modalité d'admission : ces faits doivent venir du RAG (`rag/retriever.py`).
