"""Three classifiers, implemented with numpy only (no scikit-learn).

Rationale for a from-scratch implementation: this sandbox's network access
to PyPI was too unreliable to reproducibly install scikit-learn/scipy
(large binary wheels kept timing out — see ml/README.md). numpy was
already a project dependency (used by chromadb), so the model layer is
built directly on it: it stays 100% reproducible offline and every line of
the learning algorithm is auditable, which also serves the brief's
"traçabilité" requirement.

All three share the interface:
    fit(X, y) -> self
    predict_proba(X) -> (n_samples, n_classes) row-stochastic matrix
    classes_: list[str]

- NearestCentroidBaseline: the "modèle de référence simple" required by
  section 7 of the brief. Class prototype = mean feature vector; score =
  cosine similarity turned into a distribution via softmax.
- KNNClassifier: cosine-distance k-NN, vote weighted by similarity.
- SoftmaxRegression: multinomial logistic regression trained by full-batch
  gradient descent with L2 regularization — the main, trainable model.
"""

from __future__ import annotations

import numpy as np


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """a: (n, d), b: (m, d) -> (n, m) cosine similarities."""
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return a_norm @ b_norm.T


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    exp = np.exp(z)
    return exp / exp.sum(axis=1, keepdims=True)


class NearestCentroidBaseline:
    """Reference baseline: each class is represented by the centroid (mean
    feature vector) of its training examples; a new profile is scored by
    its cosine similarity to every centroid."""

    name = "baseline_centroide"

    def fit(self, X: np.ndarray, y: list[str]) -> "NearestCentroidBaseline":
        self.classes_ = sorted(set(y))
        self.centroids_ = np.stack(
            [X[[i for i, label in enumerate(y) if label == c]].mean(axis=0) for c in self.classes_]
        )
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        sims = _cosine_similarity(X, self.centroids_)
        return _softmax(sims * 8.0)  # temperature sharpens an otherwise flat cosine range


class KNNClassifier:
    """k-nearest-neighbours with cosine distance; votes weighted by
    similarity so probabilities are not just neighbour-count ratios."""

    name = "knn"

    def __init__(self, k: int = 15):
        self.k = k

    def fit(self, X: np.ndarray, y: list[str]) -> "KNNClassifier":
        self.classes_ = sorted(set(y))
        self._X = X
        self._y = np.array(y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        sims = _cosine_similarity(X, self._X)  # (n_query, n_train)
        k = min(self.k, sims.shape[1])
        top_idx = np.argpartition(-sims, k - 1, axis=1)[:, :k]
        out = np.zeros((X.shape[0], len(self.classes_)))
        class_index = {c: i for i, c in enumerate(self.classes_)}
        for row in range(X.shape[0]):
            for j in top_idx[row]:
                w = max(sims[row, j], 0.0) + 1e-6
                out[row, class_index[self._y[j]]] += w
        row_sums = out.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return out / row_sums


class SoftmaxRegression:
    """Multinomial logistic regression trained by full-batch gradient
    descent with L2 regularization on the cross-entropy loss."""

    name = "softmax_regression"

    def __init__(self, lr: float = 0.5, l2: float = 1e-3, epochs: int = 400, seed: int = 0):
        self.lr = lr
        self.l2 = l2
        self.epochs = epochs
        self.seed = seed

    def fit(self, X: np.ndarray, y: list[str]) -> "SoftmaxRegression":
        self.classes_ = sorted(set(y))
        class_index = {c: i for i, c in enumerate(self.classes_)}
        n, d = X.shape
        k = len(self.classes_)
        Y = np.zeros((n, k))
        for i, label in enumerate(y):
            Y[i, class_index[label]] = 1.0

        rng = np.random.default_rng(self.seed)
        self.W = rng.normal(0, 0.01, size=(d, k))
        self.b = np.zeros(k)

        self.loss_curve_: list[float] = []
        for _ in range(self.epochs):
            logits = X @ self.W + self.b
            probs = _softmax(logits)
            grad_logits = (probs - Y) / n
            grad_W = X.T @ grad_logits + self.l2 * self.W
            grad_b = grad_logits.sum(axis=0)
            self.W -= self.lr * grad_W
            self.b -= self.lr * grad_b

            eps = 1e-9
            ce = -np.sum(Y * np.log(probs + eps)) / n
            self.loss_curve_.append(float(ce + 0.5 * self.l2 * np.sum(self.W ** 2)))
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return _softmax(X @ self.W + self.b)

    def to_dict(self) -> dict:
        return {
            "type": "SoftmaxRegression",
            "classes": self.classes_,
            "W": self.W.tolist(),
            "b": self.b.tolist(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SoftmaxRegression":
        model = cls()
        model.classes_ = data["classes"]
        model.W = np.array(data["W"])
        model.b = np.array(data["b"])
        return model


def predict_labels(model, X: np.ndarray) -> list[str]:
    proba = model.predict_proba(X)
    idx = proba.argmax(axis=1)
    return [model.classes_[i] for i in idx]
