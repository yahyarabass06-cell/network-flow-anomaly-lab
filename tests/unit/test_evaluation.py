"""Verify evaluation against independently calculable examples."""

import pytest

from flow_anomaly.evaluation import evaluate_scores


def test_known_confusion_matrix():
    result = evaluate_scores(
        [0, 0, 1, 1],
        [0.1, 0.8, 0.4, 0.9],
        threshold=0.5,
    )
    assert result["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    assert result["false_positive_rate"] == 0.5
    assert result["average_precision"] == pytest.approx(5 / 6)


def test_perfect_ranking():
    result = evaluate_scores([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9], threshold=0.5)
    assert result["average_precision"] == 1
    assert result["pr_auc_trapezoidal"] == 1


def test_undefined_metrics_are_explicit():
    result = evaluate_scores([0, 0], [0.1, 0.2], threshold=0.5)
    assert result["precision"] is None
    assert result["recall"] is None
    assert result["f1"] is None
    assert result["false_positive_rate"] == 0
    assert result["average_precision"] is None
    assert "precision" in result["undefined_metrics"]


@pytest.mark.parametrize(
    ("labels", "scores"),
    [
        ([0], [0.1, 0.2]),
        ([True], [0.1]),
        ([2], [0.1]),
        ([], []),
    ],
)
def test_invalid_evaluation_input_is_rejected(labels, scores):
    with pytest.raises(ValueError):
        evaluate_scores(labels, scores, threshold=0.5)
