"""Trains and evaluates the ORIENT'IA orientation model.

The model classifies a candidate profile into a general pedagogical
orientation **domain** (ml.domaines), not directly into an ISPM filière —
see ml/domaines.py's module docstring for why. Each domain lists its
plausible ISPM filière(s) as a lookup table, used only for reporting here
and for the conversational tool's "voici les filières ISPM correspondant
à ce domaine" bridge (ml/inference.py).

Montage (as recommended by brief section 5): **train on synthetic data,
validate/test generalization on the real survey**. Concretely:

1. Generate the synthetic dataset, split 80/20 into synthetic-train /
   synthetic-val.
2. Train three models on synthetic-train: a nearest-centroid baseline
   ("modèle de référence simple", required by section 7), a k-NN
   classifier, and a multinomial logistic regression.
3. Evaluate all three on synthetic-val (in-distribution check) with
   accuracy, top-3 accuracy, macro-F1, confusion matrix, MRR, a
   calibration table and a stability score (section 7/14 requirements —
   "une simple valeur d'accuracy ne constitue pas une évaluation
   suffisante").
4. Evaluate the *selected* model's generalization on the real, usable
   survey rows, scoring a prediction correct when its top-1 (or top-3)
   falls in the row's candidate-domain set (see ml.survey) — the closest
   honest proxy available given the free-text labels and tiny sample.
5. Run a basic error analysis (worst validation mistakes) and a basic
   bias check (accuracy split by the one demographic-free attribute the
   model is allowed to use: bac série).
6. Persist the selected model + vocab as JSON (ml/artifacts/model.json)
   and write the full write-up to ml/artifacts/evaluation_report.md.

Run with: `python -m ml.train`
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

from ml.domaines import DOMAINE_IDS, DOMAINES
from ml.features import FEATURE_NAMES, encode_batch
from ml import metrics
from ml.models import KNNClassifier, NearestCentroidBaseline, SoftmaxRegression, predict_labels
from ml.survey import load_survey, usable_rows, write_anonymized_csv, write_registre
from ml.synthetic import generate_dataset, write_dataset, write_documentation

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "ml" / "artifacts"
DATA_ML = ROOT / "data" / "ml"

N_PER_CLASS = 150
SEED = 42
VAL_FRACTION = 0.2
SURVEY_PATH = ROOT / "ORIENT'IA — Réponses.xlsx"


def _train_val_split(rows: list[dict], val_fraction: float, seed: int):
    rng = random.Random(seed)
    indices = list(range(len(rows)))
    rng.shuffle(indices)
    n_val = int(len(rows) * val_fraction)
    val_idx, train_idx = set(indices[:n_val]), set(indices[n_val:])
    train = [rows[i] for i in sorted(train_idx)]
    val = [rows[i] for i in sorted(val_idx)]
    return train, val


def _rows_to_xy(rows: list[dict]):
    X = encode_batch(rows)
    y = [r["domaine_recommande"] for r in rows]
    return X, y


def _evaluate_model(name: str, model, X_val, y_val, classes) -> dict:
    proba = model.predict_proba(X_val)
    y_pred = predict_labels(model, X_val)
    return {
        "name": name,
        "accuracy": metrics.accuracy(y_val, y_pred),
        "top3_accuracy": metrics.top_k_accuracy(y_val, proba, classes, k=3),
        "macro_f1": metrics.macro_f1(y_val, y_pred, classes),
        "mrr": metrics.mean_reciprocal_rank(y_val, proba, classes),
        "stability": metrics.stability_score(model, X_val),
        "per_class": metrics.per_class_report(y_val, y_pred, classes),
        "confusion_matrix": metrics.confusion_matrix(y_val, y_pred, classes).tolist(),
        "calibration": metrics.calibration_table(y_val, proba, classes),
    }


def _error_examples(rows_val, y_val, y_pred, n=8):
    examples = []
    for row, true, pred in zip(rows_val, y_val, y_pred):
        if true != pred:
            examples.append({
                "matieres_preferees": row["matieres_preferees"],
                "centres_interet": row["centres_interet"],
                "vrai": true,
                "predit": pred,
                "label_noise": row.get("label_noise", False),
            })
        if len(examples) >= n:
            break
    return examples


def _bias_by_bac(rows_val, y_val, y_pred) -> dict:
    by_bac: dict[str, list[bool]] = {}
    for row, true, pred in zip(rows_val, y_val, y_pred):
        bac = row.get("serie_bac") or "inconnu"
        by_bac.setdefault(bac, []).append(true == pred)
    return {bac: sum(v) / len(v) for bac, v in by_bac.items()}


def _evaluate_on_survey(model, classes) -> dict:
    rows = load_survey(str(SURVEY_PATH))
    write_anonymized_csv(rows, DATA_ML / "survey" / "reponses_anonymisees.csv")
    write_registre(rows, DATA_ML / "survey" / "registre_collecte.md", SURVEY_PATH.name)

    usable = usable_rows(rows)
    if not usable:
        return {"n": 0, "note": "Aucune réponse d'enquête utilisable pour l'évaluation."}

    X = encode_batch([r.profile for r in usable])
    proba = model.predict_proba(X)

    top1_in_candidates = 0
    top3_in_candidates = 0
    details = []
    for i, row in enumerate(usable):
        ranking = [classes[j] for j in np.argsort(-proba[i])]
        top1_ok = ranking[0] in row.candidate_domaines
        top3_ok = any(c in row.candidate_domaines for c in ranking[:3])
        top1_in_candidates += top1_ok
        top3_in_candidates += top3_ok
        top1_filieres = DOMAINES[ranking[0]].ispm_filieres
        details.append({
            "respondent_id": row.respondent_id,
            "population": row.population,
            "parcours_declare": row.label_text,
            "domaines_candidats": row.candidate_domaines,
            "top3_predit": ranking[:3],
            "filieres_ispm_correspondantes": list(top1_filieres),
            "top1_dans_candidats": top1_ok,
            "top3_dans_candidats": top3_ok,
        })
    n = len(usable)
    return {
        "n": n,
        "top1_dans_candidats_rate": top1_in_candidates / n,
        "top3_dans_candidats_rate": top3_in_candidates / n,
        "details": details,
    }


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    # 1. Synthetic data -----------------------------------------------------
    synth_rows = generate_dataset(n_per_class=N_PER_CLASS, seed=SEED)
    write_dataset(synth_rows, DATA_ML / "synthetic" / "profils_synthetiques.csv")
    n_noisy = sum(1 for r in synth_rows if r["label_noise"])
    write_documentation(DATA_ML / "synthetic" / "generation_doc.md", N_PER_CLASS, SEED,
                         len(synth_rows), n_noisy)

    train_rows, val_rows = _train_val_split(synth_rows, VAL_FRACTION, SEED)
    X_train, y_train = _rows_to_xy(train_rows)
    X_val, y_val = _rows_to_xy(val_rows)
    classes = sorted(DOMAINE_IDS)

    # 2. Train 3 models -------------------------------------------------
    baseline = NearestCentroidBaseline().fit(X_train, y_train)
    knn = KNNClassifier(k=15).fit(X_train, y_train)
    softmax = SoftmaxRegression(lr=0.5, l2=1e-3, epochs=400, seed=SEED).fit(X_train, y_train)

    results = {
        "baseline_centroide": _evaluate_model("baseline_centroide", baseline, X_val, y_val, classes),
        "knn": _evaluate_model("knn", knn, X_val, y_val, classes),
        "softmax_regression": _evaluate_model("softmax_regression", softmax, X_val, y_val, classes),
    }

    # Select the best model by macro-F1 on the synthetic validation split.
    best_name = max(results, key=lambda k: results[k]["macro_f1"])
    best_model = {"baseline_centroide": baseline, "knn": knn, "softmax_regression": softmax}[best_name]

    y_pred_best = predict_labels(best_model, X_val)
    error_examples = _error_examples(val_rows, y_val, y_pred_best)
    bias_by_bac = _bias_by_bac(val_rows, y_val, y_pred_best)

    # 3. Real-survey generalization check --------------------------------
    survey_eval = _evaluate_on_survey(best_model, classes)

    # 4. Persist artifacts ------------------------------------------------
    artifact = {
        "selected_model": best_name,
        "classes": classes,
        "feature_names": FEATURE_NAMES,
        "softmax_regression": softmax.to_dict(),
    }
    with open(ARTIFACTS / "model.json", "w", encoding="utf-8") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=2)

    report = {
        "selected_model": best_name,
        "n_train": len(train_rows),
        "n_val": len(val_rows),
        "results_on_synthetic_val": results,
        "error_examples": error_examples,
        "bias_by_serie_bac": bias_by_bac,
        "survey_generalization": survey_eval,
    }
    with open(ARTIFACTS / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    _write_markdown_report(report, ARTIFACTS / "evaluation_report.md")
    print(f"Modèle sélectionné : {best_name}")
    print(f"Accuracy val (synthétique) : {results[best_name]['accuracy']:.3f}")
    print(f"Top-3 accuracy val (synthétique) : {results[best_name]['top3_accuracy']:.3f}")
    if survey_eval["n"]:
        print(f"Généralisation enquête réelle (n={survey_eval['n']}) — "
              f"top-1 dans candidats : {survey_eval['top1_dans_candidats_rate']:.3f}")
    print(f"Artifacts écrits dans {ARTIFACTS}")


def _write_markdown_report(report: dict, path: Path) -> None:
    r = report["results_on_synthetic_val"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Rapport d'évaluation — Machine Learning ORIENT'IA\n\n")
        f.write(
            "Généré par `python -m ml.train`. Le modèle classe un profil "
            "parmi 15 **domaines d'orientation pédagogique généraux** "
            "(`ml.domaines`), pas directement parmi les filières ISPM — "
            "voir `ml/domaines.py` pour la justification. Montage : "
            "entraînement sur données synthétiques, validation sur un "
            "split synthétique tenu à part, test de généralisation sur les "
            "réponses réelles de l'enquête (voir "
            "`data/ml/survey/registre_collecte.md`).\n\n"
        )
        f.write(f"- Profils d'entraînement (synthétiques) : {report['n_train']}\n")
        f.write(f"- Profils de validation (synthétiques, tenus à part) : {report['n_val']}\n")
        f.write(f"- **Modèle sélectionné (meilleur macro-F1 en validation) : `{report['selected_model']}`**\n\n")

        f.write("## Comparaison des approches (validation synthétique)\n\n")
        f.write("| Modèle | Accuracy | Top-3 accuracy | Macro-F1 | MRR | Stabilité |\n")
        f.write("|---|---|---|---|---|---|\n")
        for name, res in r.items():
            f.write(
                f"| {name} | {res['accuracy']:.3f} | {res['top3_accuracy']:.3f} | "
                f"{res['macro_f1']:.3f} | {res['mrr']:.3f} | {res['stability']:.3f} |\n"
            )
        f.write(
            "\n`baseline_centroide` est le modèle de référence simple exigé "
            "par le brief (section 7). `stabilité` = fraction des profils "
            "dont le top-1 ne change pas sous une petite perturbation "
            "gaussienne du vecteur de traits (voir `ml.metrics.stability_score`).\n"
        )

        best = r[report["selected_model"]]
        f.write(f"\n## Détail du modèle sélectionné (`{report['selected_model']}`)\n\n")
        f.write("### Rapport par domaine (precision / recall / F1 / support)\n\n")
        f.write("| Domaine | Precision | Recall | F1 | Support |\n|---|---|---|---|---|\n")
        for code, m in best["per_class"].items():
            label = DOMAINES[code].label
            f.write(f"| {code} — {label} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} | {m['support']} |\n")

        f.write("\n### Table de calibration (confiance du top-1 vs exactitude empirique)\n\n")
        f.write("| Intervalle de confiance | n | Confiance moyenne | Exactitude empirique |\n|---|---|---|---|\n")
        for row in best["calibration"]:
            conf = f"{row['confiance_moyenne']:.2f}" if row["confiance_moyenne"] is not None else "n/a"
            acc = f"{row['exactitude_empirique']:.2f}" if row["exactitude_empirique"] is not None else "n/a"
            f.write(f"| {row['intervalle']} | {row['n']} | {conf} | {acc} |\n")

        f.write("\n### Matrice de confusion (lignes = vrai, colonnes = prédit)\n\n")
        classes = sorted(DOMAINES.keys())
        f.write("| | " + " | ".join(classes) + " |\n")
        f.write("|---|" + "---|" * len(classes) + "\n")
        for i, code in enumerate(classes):
            f.write(f"| **{code}** | " + " | ".join(str(v) for v in best["confusion_matrix"][i]) + " |\n")

        f.write("\n### Analyse d'erreurs (exemples de validation mal classés)\n\n")
        if report["error_examples"]:
            for ex in report["error_examples"]:
                noise_flag = " *(étiquette bruitée par construction)*" if ex["label_noise"] else ""
                f.write(
                    f"- Matières = « {ex['matieres_preferees']} », intérêts = "
                    f"« {ex['centres_interet']} » → vrai **{ex['vrai']}**, "
                    f"prédit **{ex['predit']}**{noise_flag}\n"
                )
        else:
            f.write("Aucune erreur sur l'échantillon de validation retenu pour l'exemple.\n")

        f.write(
            "\n### Étude de biais\n\n"
            "Aucun attribut démographique (genre, âge, origine) n'est "
            "utilisé par le modèle — choix de conception, pas absence de "
            "signal disponible (brief section 16). Le seul attribut de "
            "profil scolaire disponible, la série du baccalauréat, sert de "
            "sous-groupe pour vérifier que l'exactitude du modèle ne "
            "s'effondre pas sur un sous-groupe particulier :\n\n"
        )
        f.write("| Série bac | Exactitude (sous-groupe) |\n|---|---|\n")
        for bac, acc in report["bias_by_serie_bac"].items():
            f.write(f"| {bac} | {acc:.2f} |\n")

        f.write("\n## Généralisation : évaluation sur l'enquête réelle\n\n")
        survey = report["survey_generalization"]
        if survey["n"] == 0:
            f.write(f"{survey.get('note', 'Aucune donnée.')}\n")
        else:
            f.write(
                f"- Réponses d'enquête utilisables : **{survey['n']}**\n"
                f"- Top-1 prédit ∈ domaines candidats du répondant : "
                f"**{survey['top1_dans_candidats_rate']:.0%}**\n"
                f"- Top-3 prédit ∩ domaines candidats ≠ ∅ : "
                f"**{survey['top3_dans_candidats_rate']:.0%}**\n\n"
            )
            f.write(
                "> **Limite majeure à ne pas masquer** : cet échantillon ne "
                f"compte que {survey['n']} réponses, toutes de la population "
                "étudiante/lycéenne (aucun professionnel à ce jour), et le "
                "« domaine candidat » est lui-même déduit du texte libre du "
                "répondant par correspondance de mots-clés — voir "
                "`ml.survey.map_to_candidate_domaines`. Ce chiffre est un "
                "indicateur de cohérence grossier, pas une estimation fiable "
                "du taux de généralisation réel. Il devra être recalculé à "
                "mesure que l'enquête collecte davantage de réponses "
                "(idéalement avant le gel de fin de première journée prévu "
                "par le brief).\n\n"
            )
            f.write(
                "| Répondant | Population | Parcours déclaré | Domaines candidats | "
                "Top-3 prédit | Filières ISPM (top-1) | Top-1 ok | Top-3 ok |\n"
            )
            f.write("|---|---|---|---|---|---|---|---|\n")
            for d in survey["details"]:
                f.write(
                    f"| {d['respondent_id']} | {d['population']} | {d['parcours_declare']} | "
                    f"{', '.join(d['domaines_candidats'])} | {', '.join(d['top3_predit'])} | "
                    f"{', '.join(d['filieres_ispm_correspondantes'])} | "
                    f"{'✅' if d['top1_dans_candidats'] else '❌'} | "
                    f"{'✅' if d['top3_dans_candidats'] else '❌'} |\n"
                )

        f.write(
            "\n## Limites générales du jeu de données et du modèle\n\n"
            "- Les profils synthétiques encodent des hypothèses de "
            "conception (affinités matière/domaine choisies à la main) — "
            "voir `data/ml/synthetic/generation_doc.md`. Une performance "
            "élevée en validation synthétique mesure surtout la capacité du "
            "modèle à retrouver ces règles, pas sa validité sur une "
            "population réelle — d'où le test de généralisation ci-dessus.\n"
            "- Le trait de personnalité auto-déclaré (« caractère ») collecté "
            "par l'enquête n'est jamais utilisé comme variable d'entrée, "
            "conformément à l'interdiction de profilage psychologique du "
            "brief.\n"
            "- Le modèle prédit un **domaine d'orientation général**, pas "
            "directement une filière ISPM : la correspondance domaine → "
            "filière(s) ISPM (`ml.domaines.DOMAINES[...].ispm_filieres`) est "
            "une table de correspondance fixe, pas une prédiction du "
            "modèle. Ni le modèle ni le LLM n'inventent de débouché, de "
            "prérequis ou de modalité d'admission : ces faits doivent venir "
            "du RAG (`rag/retriever.py`).\n"
        )


if __name__ == "__main__":
    main()
