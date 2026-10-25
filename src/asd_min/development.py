# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Score Development submissions from the labels in their test filenames.

Development is the split used to choose configurations (Dev7); Evaluation is
reported only. The metric follows the DCASE 2026 Task 2 official score:

AUC_source = AUC on source normal clips and all anomalous clips
AUC_target = AUC on target normal clips and all anomalous clips
pAUC       = AUC up to FPR 0.1 (McClish-standardized) on all clips
machine    = hmean(AUC_source, AUC_target, pAUC)
Dev7       = hmean of the 3 values of all 7 machines (21 values)
Dev5       = the same without ToyCar and ToyCarEmu (15 values)
"""

import csv
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from .protocol import (
    DEV5_EXCLUDED,
    DEV_TEST_FILENAME,
    DEVELOPMENT_MACHINES,
    PAUC_MAX_FPR,
    TEST_CLIPS,
)


def parse_test_labels(filenames):
    """Domain and label of each Development test clip from its filename.

    Args:
        filenames: ``[N]`` names such as
            ``section_00_target_test_anomaly_0005_noAttribute.wav``.

    Returns:
        ``(is_target, is_normal)``: two boolean ``[N]`` arrays.
    """
    matches = [DEV_TEST_FILENAME.fullmatch(name) for name in filenames]
    if not all(matches):
        raise ValueError("Development test filenames must carry domain and label")
    is_target = np.array([m["domain"] == "target" for m in matches])
    is_normal = np.array([m["label"] == "normal" for m in matches])
    return is_target, is_normal


def domain_mask(domain, is_target, is_normal):
    """Clips used for one metric: a domain's normal clips plus all anomalies.

    Args:
        domain: ``"source"``, ``"target"`` or ``"mix"`` (every clip).
        is_target: ``[N]`` booleans.
        is_normal: ``[N]`` booleans.

    Returns:
        ``[N]`` boolean mask.
    """
    if domain == "source":
        return ~is_target | ~is_normal
    if domain == "target":
        return is_target | ~is_normal
    if domain == "mix":
        return np.ones_like(is_normal, dtype=bool)
    raise ValueError(f"Unknown domain: {domain!r}")


def harmonic_mean(values):
    """hmean(x) = n / sum(1 / x) for positive values."""
    values = np.asarray(values, dtype=np.float64)
    if (values <= 0).any():
        raise ValueError("Harmonic mean needs positive values")
    return float(len(values) / np.sum(1.0 / values))


def machine_metrics(filenames, scores):
    """AUC_source, AUC_target, pAUC and their harmonic mean for one machine.

    Args:
        filenames: ``[N]`` Development test filenames.
        scores: ``[N]`` anomaly scores; larger means more anomalous.

    Returns:
        ``{"auc_source", "auc_target", "pauc", "official"}`` as floats.
    """
    scores = np.asarray(scores, dtype=np.float64)
    is_target, is_normal = parse_test_labels(filenames)
    is_anomaly = (~is_normal).astype(int)
    metrics = {}
    for name, domain, max_fpr in [
        ("auc_source", "source", None),
        ("auc_target", "target", None),
        ("pauc", "mix", PAUC_MAX_FPR),
    ]:
        mask = domain_mask(domain, is_target, is_normal)
        metrics[name] = float(
            roc_auc_score(is_anomaly[mask], scores[mask], max_fpr=max_fpr)
        )
    metrics["official"] = harmonic_mean(
        [metrics["auc_source"], metrics["auc_target"], metrics["pauc"]]
    )
    return metrics


def read_scores(system, machine):
    """Read ``anomaly_score_<machine>_section_00_test.csv`` as (filenames, scores)."""
    path = Path(system) / f"anomaly_score_{machine}_section_00_test.csv"
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) != TEST_CLIPS or any(len(row) != 2 for row in rows):
        raise ValueError(f"{path.name}: expected {TEST_CLIPS} rows of two columns")
    return [row[0] for row in rows], [float(row[1]) for row in rows]


def score_development(system, machines=DEVELOPMENT_MACHINES):
    """Per-machine metrics and Dev7/Dev5 for one condition's submission.

    Args:
        system: Directory with the condition's Development anomaly-score CSVs.
        machines: Development machines to score; Dev7 needs all seven.

    Returns:
        ``(rows, summary)``: one metrics dictionary per machine (with
        ``"machine"``), and ``{"dev7": ..., "dev5": ...}``. A summary entry is
        None when one of its machines is missing from ``machines``.
    """
    rows = []
    for machine in machines:
        rows.append(
            {"machine": machine, **machine_metrics(*read_scores(system, machine))}
        )
    by_machine = {row["machine"]: row for row in rows}
    keys = ("auc_source", "auc_target", "pauc")
    summary = {}
    for name, subset in [
        ("dev7", DEVELOPMENT_MACHINES),
        ("dev5", tuple(m for m in DEVELOPMENT_MACHINES if m not in DEV5_EXCLUDED)),
    ]:
        if all(machine in by_machine for machine in subset):
            values = [by_machine[m][k] for m in subset for k in keys]
            summary[name] = harmonic_mean(values)
        else:
            summary[name] = None
    return rows, summary
