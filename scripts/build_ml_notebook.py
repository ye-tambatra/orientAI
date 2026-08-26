"""One-off script that generates ml/notebooks/01_eda_et_entrainement.ipynb.

Not part of the runtime pipeline — run once (or whenever the notebook's
content needs regenerating) with: python scripts/build_ml_notebook.py
"""

import json
from pathlib import Path


def md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}


def code(src: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": src.splitlines(keepends=True),
    }


cells = [
    md(
        "# ORIENT'IA — Analyse et entraînement du modèle de Machine Learning\n"
        "\n"
        "Ce notebook rejoue, cellule par cellule, le pipeline implémenté sous "
        "`ml/` : génération des données synthétiques, analyse exploratoire, "
        "entraînement et comparaison de trois approches, évaluation sur un "
        "split de validation puis sur l'enquête réelle. Exécuter les "
        "cellules dans l'ordre depuis la racine du dépôt (kernel Python de "
        "`venv/`).\n"
        "\n"
        "Le détail méthodologique (hypothèses, biais, contrôles) est "
        "documenté dans le code (`ml/synthetic.py`, `ml/survey.py`) et dans "
        "`ml/artifacts/evaluation_report.md` — ce notebook en donne une vue "
        "exécutable, pas une redite."
    ),
    md("## 1. Génération des données synthétiques (jeu d'entraînement)"),
    code(
        "import sys\n"
        "sys.path.insert(0, '..')\n"
        "\n"
        "from ml.synthetic import generate_dataset\n"
        "from ml.domaines import DOMAINE_IDS\n"
        "\n"
        "rows = generate_dataset(n_per_class=150, seed=42)\n"
        "print(f\"{len(rows)} profils générés pour {len(DOMAINE_IDS)} domaines d'orientation\")\n"
        "rows[0]"
    ),
    md(
        "## 2. Analyse exploratoire\n"
        "\n"
        "Vérification de l'équilibre des classes, du taux d'étiquettes "
        "bruitées introduites volontairement (voir la docstring de "
        "`ml.synthetic`), et de la fréquence des tags générés."
    ),
    code(
        "from collections import Counter\n"
        "\n"
        "label_counts = Counter(r['domaine_recommande'] for r in rows)\n"
        "print('Profils par domaine (doit être ~équilibré) :')\n"
        "for code_, n in sorted(label_counts.items()):\n"
        "    print(f'  {code_}: {n}')\n"
        "\n"
        "n_noisy = sum(1 for r in rows if r['label_noise'])\n"
        "print(f\"\\nProfils à étiquette bruitée : {n_noisy} ({n_noisy/len(rows):.1%})\")"
    ),
    code(
        "matiere_tokens = Counter()\n"
        "for r in rows:\n"
        "    for tag in r['matieres_preferees'].split(', '):\n"
        "        if tag:\n"
        "            matiere_tokens[tag] += 1\n"
        "matiere_tokens.most_common(10)"
    ),
    md(
        "## 3. Préparation des features et séparation train/validation\n"
        "\n"
        "Encodage multi-hot des matières/compétences/intérêts déclarés + "
        "one-hot environnement/série de bac (`ml.features.encode_batch`). "
        "Split 80/20 reproductible (même graine que `ml.train`)."
    ),
    code(
        "from ml.train import _train_val_split, _rows_to_xy, N_PER_CLASS, SEED, VAL_FRACTION\n"
        "\n"
        "train_rows, val_rows = _train_val_split(rows, VAL_FRACTION, SEED)\n"
        "X_train, y_train = _rows_to_xy(train_rows)\n"
        "X_val, y_val = _rows_to_xy(val_rows)\n"
        "X_train.shape, X_val.shape"
    ),
    md(
        "## 4. Modèle de référence simple, puis comparaison de deux approches\n"
        "\n"
        "- `NearestCentroidBaseline` : le modèle de référence exigé par le "
        "brief (section 7).\n"
        "- `KNNClassifier` : k plus proches voisins (distance cosinus).\n"
        "- `SoftmaxRegression` : régression logistique multinomiale "
        "(descente de gradient, numpy pur — voir `ml/models.py` pour la "
        "justification de l'implémentation from-scratch)."
    ),
    code(
        "from ml.models import NearestCentroidBaseline, KNNClassifier, SoftmaxRegression\n"
        "\n"
        "baseline = NearestCentroidBaseline().fit(X_train, y_train)\n"
        "knn = KNNClassifier(k=15).fit(X_train, y_train)\n"
        "softmax = SoftmaxRegression(lr=0.5, l2=1e-3, epochs=400, seed=SEED).fit(X_train, y_train)\n"
        "print('Modèles entraînés.')"
    ),
    md("## 5. Évaluation — au-delà de la simple accuracy"),
    code(
        "from ml import metrics\n"
        "from ml.models import predict_labels\n"
        "\n"
        "classes = sorted(DOMAINE_IDS)\n"
        "for name, model in [('baseline', baseline), ('knn', knn), ('softmax', softmax)]:\n"
        "    proba = model.predict_proba(X_val)\n"
        "    y_pred = predict_labels(model, X_val)\n"
        "    print(f\"{name:10s} acc={metrics.accuracy(y_val, y_pred):.3f}  \"\n"
        "          f\"top3={metrics.top_k_accuracy(y_val, proba, classes, k=3):.3f}  \"\n"
        "          f\"macroF1={metrics.macro_f1(y_val, y_pred, classes):.3f}  \"\n"
        "          f\"MRR={metrics.mean_reciprocal_rank(y_val, proba, classes):.3f}  \"\n"
        "          f\"stabilite={metrics.stability_score(model, X_val):.3f}\")"
    ),
    code(
        "import numpy as np\n"
        "\n"
        "y_pred_softmax = predict_labels(softmax, X_val)\n"
        "cm = metrics.confusion_matrix(y_val, y_pred_softmax, classes)\n"
        "print('Matrice de confusion (softmax), lignes=vrai, colonnes=prédit:')\n"
        "print(np.array2string(cm, max_line_width=200))"
    ),
    md(
        "## 6. Généralisation vers l'enquête réelle\n"
        "\n"
        "Montage recommandé par le brief : entraînement sur synthétique, "
        "test de généralisation sur les réponses réelles collectées "
        "(`ORIENT'IA — Réponses.xlsx`). Voir `data/ml/survey/registre_collecte.md` "
        "pour la traçabilité complète de cette collecte, et la limite "
        "explicite sur sa taille."
    ),
    code(
        "from ml.train import _evaluate_on_survey\n"
        "\n"
        "survey_eval = _evaluate_on_survey(softmax, classes)\n"
        "survey_eval"
    ),
    md(
        "## 7. Artifacts produits\n"
        "\n"
        "`python -m ml.train` régénère automatiquement :\n"
        "- `ml/artifacts/model.json` — modèle sélectionné (softmax), rechargé "
        "par `ml/inference.py` pour les outils de l'agent conversationnel ;\n"
        "- `ml/artifacts/evaluation_results.json` / `evaluation_report.md` — "
        "le rapport complet (comparaison des 3 approches, calibration, "
        "biais, erreurs, généralisation) ;\n"
        "- `data/ml/synthetic/` et `data/ml/survey/` — les jeux de données et "
        "leur documentation/registre de traçabilité."
    ),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = Path(__file__).resolve().parent.parent / "ml" / "notebooks" / "01_eda_et_entrainement.ipynb"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Wrote {out}")
