"""Binary evaluation with explicit handling of undefined metrics."""

import numpy as np
from sklearn.metrics import (
    auc,
    average_precision_score,
    precision_recall_curve,
)

from flow_anomaly.calibration import predict_anomalies, validate_scores


def evaluate_scores(labels, scores, *, threshold: float) -> dict:
    scores = validate_scores(scores)
    labels = tuple(labels)
    if len(labels) != len(scores):
        raise ValueError("Labels and scores must have matching lengths.")
    if any(type(label) is not int or label not in (0, 1) for label in labels):
        raise ValueError("Labels must be integer zero or one.")

    truth = np.asarray(labels, dtype=np.int64)
    predicted = predict_anomalies(scores, threshold=threshold)

    tp = int(np.sum((truth == 1) & predicted))
    fp = int(np.sum((truth == 0) & predicted))
    tn = int(np.sum((truth == 0) & ~predicted))
    fn = int(np.sum((truth == 1) & ~predicted))
    undefined = []

    def ratio(name, numerator, denominator):
        if denominator == 0:
            undefined.append(name)
            return None
        return numerator / denominator

    precision = ratio("precision", tp, tp + fp)
    recall = ratio("recall", tp, tp + fn)
    f1 = ratio("f1", 2 * tp, 2 * tp + fp + fn)
    fpr = ratio("false_positive_rate", fp, fp + tn)

    # Ranking evaluation requires both classes in this project's protocol.
    if set(labels) == {0, 1}:
        ap = float(average_precision_score(truth, scores))
        curve_precision, curve_recall, _ = precision_recall_curve(truth, scores)
        pr_auc = float(auc(curve_recall, curve_precision))
    else:
        ap = pr_auc = None
        undefined.extend(("average_precision", "pr_auc_trapezoidal"))

    return {
        "records": len(labels),
        "positive_label": 1,
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
        "average_precision": ap,
        "pr_auc_trapezoidal": pr_auc,
        "undefined_metrics": undefined,
    }
