# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Invoke reader-provided official evaluator only after their terms review.
No evaluator source or truth CSV is included in this distribution.
"""

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

from .protocol import EVALUATOR_REVISION as REVISION
from .protocol import MACHINES, TEST_CLIPS, TEST_FILENAMES
from .runner import digest


def validate(system):
    """Check one condition's submission: 5 machines x 2 CSVs, 200 finite rows each.

    Args:
        system: Directory with the condition's ``anomaly_score_*`` and
            ``decision_result_*`` CSVs.

    Returns:
        The set of expected filenames.

    Raises:
        ValueError: A file is missing, extra, or has wrong rows or values.
    """
    system = Path(system)
    expected = set()
    for machine in MACHINES:
        for prefix in ("anomaly_score", "decision_result"):
            name = f"{prefix}_{machine}_section_00_test.csv"
            expected.add(name)
            with (system / name).open() as f:
                rows = list(csv.reader(f))
            if len(rows) != TEST_CLIPS or any(len(r) != 2 for r in rows):
                raise ValueError(name)
            if {r[0] for r in rows} != TEST_FILENAMES:
                raise ValueError("Filename mismatch")
            for _, value in rows:
                x = float(value)
                if not math.isfinite(x) or (
                    prefix == "decision_result" and x not in (0, 1)
                ):
                    raise ValueError("Invalid score")
    submitted = {p.name for p in system.glob("anomaly_score_*.csv")} | {
        p.name for p in system.glob("decision_result_*.csv")
    }
    if submitted != expected:
        raise ValueError("Unexpected submission files")
    return expected


def _check_evaluator(evaluator):
    """Require the pinned evaluator revision with a clean working tree."""
    revision = subprocess.check_output(
        ["git", "-C", str(evaluator), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != REVISION:
        raise ValueError("Wrong evaluator revision")
    if subprocess.check_output(
        ["git", "-C", str(evaluator), "status", "--porcelain"], text=True
    ).strip():
        raise ValueError("Evaluator must be unmodified and clean")


def evaluate(system, evaluator, output, terms_reviewed=False):
    """Score one condition's submission with the reader-provided official evaluator.

    Args:
        system: Submission directory (checked by ``validate``).
        evaluator: Clean checkout of the evaluator at ``EVALUATOR_REVISION``.
        output: New output directory for the log, results and receipt.
        terms_reviewed: Must be True once the reader has reviewed the
            evaluator's terms of use.

    Returns:
        Path of the evaluator's result CSV.
    """
    if not terms_reviewed:
        raise ValueError(
            "Review evaluator conditions yourself first; see docs/rights.md"
        )
    system, evaluator, output = (Path(x).resolve() for x in (system, evaluator, output))
    validate(system)
    _check_evaluator(evaluator)
    if output.exists():
        raise ValueError("Refusing to overwrite")
    output.mkdir(parents=True)
    stage = output / "teams" / "reader"
    stage.mkdir(parents=True)
    (stage / system.name).symlink_to(system, target_is_directory=True)
    command = [
        sys.executable, str(evaluator / "dcase2026_task2_evaluator.py"),
        "--teams_root_dir", str(output / "teams"), "--dir_depth", "2",
        "--result_dir", str(output / "results"), "--out_all", "True",
        "--additional_result_dir", str(output / "additional"),
    ]  # fmt: skip
    receipt = {
        "revision": REVISION,
        "status": "running",
        "submission_sha256": {p.name: digest(p) for p in system.glob("*score_*.csv")},
    }
    try:
        with (output / "evaluator.log").open("w") as log:
            subprocess.run(
                command, cwd=evaluator, stdout=log, stderr=subprocess.STDOUT, check=True
            )
        receipt["status"] = "succeeded"
    except Exception:
        receipt["status"] = "failed"
        raise
    finally:
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return output / "results" / f"{system.name}_result.csv"
