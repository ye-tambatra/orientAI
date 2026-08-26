"""Evaluation metrics for the ML component.

The brief explicitly rules out reporting accuracy alone (section 7). This
module provides accuracy, top-k accuracy, macro precision/recall/F1, a
confusion matrix, Mean Reciprocal Rank, a calibration table and a
stability score, all computed with numpy/stdlib only.
"""

from __future__ import annotations

import numpy as np


def accuracy(y_true: list[str], y_pred: list[str]) -> float:
    return float(np.mean([t == p for t, p in zip(y_true, y_pred)]))


def top_k_accuracy(y_true: list[str], proba: np.ndarray, classes: list[str], k: int = 3) -> float:
    class_index = {c: i for i, c in enumerate(classes)}
    hits = 0
    for i, true_label in enumerate(y_true):
        top_k = np.argsort(-proba[i])[:k]
        if class_index[true_label] in top_k:
            hits += 1
    return hits / len(y_true) if y_true else 0.0


def confusion_matrix(y_true: list[str], y_pred: list[str], classes: list[str]) -> np.ndarray:
    index = {c: i for i, c in enumerate(classes)}
    m = np.zeros((len(classes), len(classes)), dtype=int)
    for t, p in zip(y_true, y_pred):
        m[index[t], index[p]] += 1
    return m


def per_class_report(y_true: list[str], y_pred: list[str], classes: list[str]) -> dict[str, dict[str, float]]:
    cm = confusion_matrix(y_true, y_pred, classes)
    report = {}
    for i, c in enumerate(classes):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        support = cm[i, :].sum()
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        report[c] = {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "support": int(support),
        }
    return report


def macro_f1(y_true: list[str], y_pred: list[str], classes: list[str]) -> float:
    report = per_class_report(y_true, y_pred, classes)
    present = [c for c in classes if report[c]["support"] > 0]
    if not present:
        return 0.0
    return float(np.mean([report[c]["f1"] for c in present]))


def mean_reciprocal_rank(y_true: list[str], proba: np.ndarray, classes: list[str]) -> float:
    class_index = {c: i for i, c in enumerate(classes)}
    reciprocal_ranks = []
    for i, true_label in enumerate(y_true):
        ranking = np.argsort(-proba[i])
        rank = int(np.where(ranking == class_index[true_label])[0][0]) + 1
        reciprocal_ranks.append(1.0 / rank)
    return float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0


def calibration_table(y_true: list[str], proba: np.ndarray, classes: list[str],
                       bins: tuple[float, ...] = (0.0, 0.3, 0.5, 0.7, 0.9, 1.0)) -> list[dict]:
    """Buckets the model's top-1 confidence and reports empirical accuracy
    in each bucket (a coarse reliability diagram in table form)."""
    class_index = {c: i for i, c in enumerate(classes)}
    top1_conf = proba.max(axis=1)
    top1_pred = proba.argmax(axis=1)
    correct = np.array([
        top1_pred[i] == class_index[y_true[i]] for i in range(len(y_true))
    ])
    table = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (top1_conf >= lo) & (top1_conf < hi if hi < 1.0 else top1_conf <= hi)
        n = int(mask.sum())
        table.append({
            "intervalle": f"[{lo:.1f}, {hi:.1f}{']' if hi >= 1.0 else ')'}",
            "n": n,
            "confiance_moyenne": float(top1_conf[mask].mean()) if n else None,
            "exactitude_empirique": float(correct[mask].mean()) if n else None,
        })
    return table


def stability_score(model, X: np.ndarray, n_trials: int = 5, noise_std: float = 0.15,
                     seed: int = 0) -> float:
    """Fraction of profiles whose top-1 recommendation is unchanged when a
    small amount of Gaussian noise is added to the feature vector — a
    proxy for "does a barely-different profile flip the recommendation?"
    """
    rng = np.random.default_rng(seed)
    base_pred = model.predict_proba(X).argmax(axis=1)
    same = np.zeros(X.shape[0])
    for _ in range(n_trials):
        noisy = X + rng.normal(0, noise_std, size=X.shape)
        noisy = np.clip(noisy, 0.0, None)
        pred = model.predict_proba(noisy).argmax(axis=1)
        same += (pred == base_pred)
    return float(np.mean(same / n_trials))
