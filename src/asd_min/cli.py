# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Command line for article 2: view stored results, run inference, or rescore."""

import argparse
import csv
import json
from pathlib import Path

from .protocol import CONDITIONS, DATASET_MACHINES


def main():
    """Parse ``results`` / ``infer`` / ``score-dev`` / ``evaluate`` and run it."""
    parser = argparse.ArgumentParser(
        description="ASD experiments: article 2 B0/B1/W1/SS"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    view = sub.add_parser(
        "results", help="View saved experiment results; no inference or rescoring"
    )
    view.add_argument("--file", type=Path, default=Path("results/02-summary.csv"))
    infer = sub.add_parser(
        "infer", help="New features and normal references per condition"
    )
    infer.add_argument("--input", type=Path, required=True)
    infer.add_argument("--checkpoint", type=Path, required=True)
    infer.add_argument("--output", type=Path, required=True)
    infer.add_argument(
        "--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS)
    )
    infer.add_argument(
        "--dataset",
        choices=tuple(DATASET_MACHINES),
        default="eval",
        help="dev: choose configurations (Dev7); eval: report only",
    )
    infer.add_argument("--device", default="cpu")
    infer.add_argument(
        "--machine", choices=sorted({m for v in DATASET_MACHINES.values() for m in v})
    )
    infer.add_argument("--limit", type=int, help="Smoke only; never an article score")
    infer.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inventory and show count; no checkpoint loading",
    )
    dev = sub.add_parser(
        "score-dev", help="Dev7/Dev5 from labeled Development test filenames"
    )
    dev.add_argument("--system", type=Path, required=True)
    dev.add_argument("--output", type=Path, help="Optional per-machine CSV")
    ev = sub.add_parser(
        "evaluate", help="Requires reader-provided evaluator and resolved terms"
    )
    ev.add_argument("--system", type=Path, required=True)
    ev.add_argument("--evaluator", type=Path, required=True)
    ev.add_argument("--output", type=Path, required=True)
    ev.add_argument("--terms-reviewed", action="store_true")
    args = parser.parse_args()
    if args.command == "results":
        with args.file.open() as f:
            for row in csv.DictReader(f):
                score = 100 * float(row["official_score"])
                print(
                    f"{row['condition'].upper()}: {score:.3f} (stored experiment result; no computation in this command)"
                )
    elif args.command == "infer":
        from .runner import plan, run

        machines = (args.machine,) if args.machine else DATASET_MACHINES[args.dataset]
        if args.dry_run:
            files = plan(args.input, machines, args.limit, args.dataset)
            print(
                json.dumps(
                    {m: {s: len(p) for s, p in v.items()} for m, v in files.items()},
                    indent=2,
                )
            )
        else:
            receipt = run(
                args.input,
                args.checkpoint,
                args.output,
                args.conditions,
                args.device,
                machines,
                args.limit,
                args.dataset,
            )
            print(json.dumps(receipt, indent=2))
    elif args.command == "score-dev":
        from .development import score_development

        rows, summary = score_development(args.system)
        if args.output:
            with args.output.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        for row in rows:
            print(f"{row['machine']}: {100 * row['official']:.3f}")
        for name, value in summary.items():
            print(f"{name.upper()}: {100 * value:.3f}")
    else:
        from .evaluation import evaluate

        print(evaluate(args.system, args.evaluator, args.output, args.terms_reviewed))


if __name__ == "__main__":
    main()
