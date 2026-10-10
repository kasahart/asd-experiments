# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Small serial inference path. Every condition fits its own normal memory.

One function per step in runner.md: plan inputs, extract features, score one
machine, write its submission files. ``run`` only orders the steps.
"""

import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch

from .beam import BEAMVarianceMin
from .pooling import frequency_pooling, sequence_to_time_frequency
from .protocol import (
    CHECKPOINT_SHA256,
    CONDITIONS,
    DATASET_MACHINES,
    DEV_TEST_FILENAME,
    MACHINES,
    RDP_GAMMA,
    SMOKE_MIN_REFERENCES,
    SOURCE_TRAIN_CLIPS,
    TARGET_TRAIN_CLIPS,
    TEST_CLIPS,
    TEST_FILENAMES,
    THRESHOLD_QUANTILE,
    TRAIN_CLIPS,
    VARMIN_K,
)
from .waveform import condition_audio, load_audio


def digest(path):
    """SHA-256 hex digest of a file, read in 1 MiB chunks."""
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def plan(root, machines=MACHINES, limit=None, dataset="eval"):
    """Check the fixed train/test inventory and return the files per machine.

    Args:
        root: Directory holding ``<machine>/train`` and ``<machine>/test``.
        machines: Machines of ``dataset`` to include.
        limit: Keep only the first ``limit`` files per split (smoke runs only).
        dataset: ``"eval"`` (anonymous test names) or ``"dev"`` (test names
            carrying domain and normal/anomaly labels).

    Returns:
        ``{machine: {"train": [Path, ...], "test": [Path, ...]}}`` sorted by name.

    Raises:
        ValueError: Counts (1000 train with 990 source / 10 target, 200 test)
            or test filenames differ from the protocol.
    """
    if dataset not in DATASET_MACHINES:
        raise ValueError(f"Unknown dataset: {dataset!r}")
    root = Path(root)
    selected = {}
    for machine in machines:
        if machine not in DATASET_MACHINES[dataset]:
            raise ValueError(f"{machine} is not in the {dataset} dataset")
        selected[machine] = {}
        for split, count in [("train", TRAIN_CLIPS), ("test", TEST_CLIPS)]:
            paths = sorted((root / machine / split).glob("*.wav"))
            if len(paths) != count:
                raise ValueError(
                    f"{machine}/{split}: expected {count}, got {len(paths)}"
                )
            if split == "train":
                if any("_train_normal_" not in p.name for p in paths):
                    raise ValueError("Normal training filenames required")
                source = sum("_source_train_normal_" in p.name for p in paths)
                target = sum("_target_train_normal_" in p.name for p in paths)
                if source != SOURCE_TRAIN_CLIPS or target != TARGET_TRAIN_CLIPS:
                    raise ValueError(
                        f"Expected {SOURCE_TRAIN_CLIPS} source and "
                        f"{TARGET_TRAIN_CLIPS} target normal training clips"
                    )
            if split == "test" and dataset == "eval":
                if {p.name for p in paths} != TEST_FILENAMES:
                    raise ValueError("Keep original anonymous Evaluation filenames")
            if split == "test" and dataset == "dev":
                if not all(DEV_TEST_FILENAME.fullmatch(p.name) for p in paths):
                    raise ValueError("Keep original labeled Development filenames")
            selected[machine][split] = paths[:limit] if limit else paths
    return selected


class Encoder:
    """Frozen BEATs_iter3 followed by frequency-preserving RDP: one [F, D] per clip.

    Args:
        checkpoint: BEATs_iter3 checkpoint; its SHA-256 must match the protocol.
        device: Torch device for inference.
    """

    def __init__(self, checkpoint, device="cpu"):
        from .beats.BEATs import BEATs, BEATsConfig

        if digest(checkpoint) != CHECKPOINT_SHA256:
            raise ValueError("Expected article BEATs_iter3 checkpoint SHA-256")
        # Official checkpoint contains config dictionaries and tensors only.
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        self.model = BEATs(BEATsConfig(payload["cfg"]))
        self.model.load_state_dict(payload["model"], strict=True)
        if self.model.predictor is not None:
            raise ValueError("Frozen sequence BEATs required")
        self.model.to(device).eval().requires_grad_(False)
        self.device = device

    @torch.inference_mode()
    def extract(self, audio):
        """Encode one waveform into band features.

        Args:
            audio: 1-channel ``[N]`` float32 waveform at 16 kHz.

        Returns:
            ``[F, D]`` RDP-pooled BEATs features as a NumPy array.
        """
        x = torch.from_numpy(np.ascontiguousarray(audio))[None].to(self.device)
        sequence, mask, grid = self.model.extract_features_with_grid(x)
        tf = sequence_to_time_frequency(sequence, grid)
        valid = None if mask is None else ~mask.reshape(1, *grid)
        pooled = frequency_pooling(
            tf, mode="rdp", gamma=RDP_GAMMA, valid_time_mask=valid
        )
        return pooled[0].cpu().numpy()


def extract_features(encoder, paths, condition, input_sha256, prefix):
    """Process each clip for the condition and encode it; record input hashes.

    Args:
        encoder: Object with ``extract(audio) -> [F, D]``.
        paths: Clip paths of one machine and split.
        condition: Condition name passed to ``condition_audio``.
        input_sha256: Dictionary updated with ``"{prefix}/{filename}": sha256``.
        prefix: ``"{machine}/{split}"`` key prefix.

    Returns:
        ``{"embed_freq": [N, F, D], "path": [N] filenames}`` for the backend.
    """
    vectors = []
    for path in paths:
        input_sha256[f"{prefix}/{path.name}"] = digest(path)
        vectors.append(encoder.extract(condition_audio(load_audio(path), condition)))
    return {"embed_freq": np.stack(vectors), "path": np.array([p.name for p in paths])}


def score_machine(train_features, test_features):
    """Fit a new BEAM+VarMin memory on this condition's normal train clips.

    Train clips are rescored without their own path. The decision threshold is
    the linear 90% point of those train scores; test labels are never used.

    Args:
        train_features: ``extract_features`` output for the train split.
        test_features: ``extract_features`` output for the test split.

    Returns:
        ``(train_scores [N_train], test_scores [N_test], threshold)``.
    """
    backend = BEAMVarianceMin(
        rescale_k=VARMIN_K, rescale_validation="train_all", rescale_scope="per_band"
    )
    backend.fit(train_features)
    train = backend.anomaly_score(train_features)["main"]
    test = backend.anomaly_score(test_features)["main"]
    threshold = float(np.quantile(train, THRESHOLD_QUANTILE, method="linear"))
    return train, test, threshold


def write_machine_outputs(folder, machine, features, train, test, threshold):
    """Write DCASE submission CSVs (strict score > threshold) and train records.

    Files in ``folder``: ``anomaly_score_<machine>_section_00_test.csv``,
    ``decision_result_<machine>_section_00_test.csv``,
    ``<machine>_train_score.csv`` and ``<machine>_threshold.json``.
    """
    for prefix, values in [
        ("anomaly_score", test),
        ("decision_result", (test > threshold).astype(int)),
    ]:
        with (folder / f"{prefix}_{machine}_section_00_test.csv").open(
            "w", newline=""
        ) as f:
            csv.writer(f).writerows(zip(features["test"]["path"], values.tolist()))
    with (folder / f"{machine}_train_score.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "score"])
        writer.writerows(zip(features["train"]["path"], train.tolist()))
    (folder / f"{machine}_threshold.json").write_text(
        json.dumps({"q90": threshold}) + "\n"
    )


def _configure_torch():
    """Two CPU threads and FP32 matmul without TF32, as in docs/02-protocol.md."""
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def run(
    root,
    checkpoint,
    output,
    conditions=CONDITIONS,
    device="cpu",
    machines=MACHINES,
    limit=None,
    dataset="eval",
):
    """Run every condition and machine and write submissions plus ``receipt.json``.

    For each condition and machine: ``extract_features`` (train, test) ->
    ``score_machine`` -> ``write_machine_outputs``. No memory is shared between
    conditions.

    Args:
        root: Raw data directory of ``dataset`` (see ``plan``).
        checkpoint: BEATs_iter3 checkpoint path.
        output: New output directory; an existing one is refused.
        conditions: Subset of ``CONDITIONS`` in run order.
        device: Torch device.
        machines: Machines of ``dataset``.
        limit: Smoke mode with at least 5 clips per split; never an article score.
        dataset: ``"eval"`` (reported only) or ``"dev"`` (for choosing configurations).

    Returns:
        The receipt dictionary also written to ``output/receipt.json``.
    """
    if limit is not None and limit < SMOKE_MIN_REFERENCES:
        raise ValueError(
            f"Smoke mode requires at least {SMOKE_MIN_REFERENCES} references"
        )
    selected = plan(root, machines, limit, dataset)
    output = Path(output)
    if output.exists():
        raise ValueError("Refusing to overwrite output")
    _configure_torch()
    encoder = Encoder(checkpoint, device)
    if str(device).startswith("cuda"):
        torch.cuda.reset_peak_memory_stats(device)
    output.mkdir(parents=True)
    receipt = {
        "status": "running",
        "mode": "smoke_not_article_score" if limit else "full",
        "dataset": dataset,
        "conditions": list(conditions),
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "torch": torch.__version__,
        "device": device,
        "input_sha256": {},
        "timings_seconds": {},
    }
    start = time.perf_counter()
    try:
        for condition in conditions:
            if condition not in CONDITIONS:
                raise ValueError(condition)
            begin = time.perf_counter()
            for machine, splits in selected.items():
                print(
                    f"{condition}/{machine}: extracting normal and test audio",
                    flush=True,
                )
                features = {
                    split: extract_features(
                        encoder,
                        paths,
                        condition,
                        receipt["input_sha256"],
                        f"{machine}/{split}",
                    )
                    for split, paths in splits.items()
                }
                # No sharing of memory across conditions, no test labels.
                train, test, threshold = score_machine(
                    features["train"], features["test"]
                )
                folder = output / condition
                folder.mkdir(exist_ok=True)
                write_machine_outputs(folder, machine, features, train, test, threshold)
            receipt["timings_seconds"][condition] = time.perf_counter() - begin
        receipt["status"] = "succeeded"
    except Exception:
        receipt["status"] = "failed"
        raise
    finally:
        receipt["elapsed_seconds"] = time.perf_counter() - start
        if str(device).startswith("cuda"):
            receipt["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated(
                device
            )
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt
