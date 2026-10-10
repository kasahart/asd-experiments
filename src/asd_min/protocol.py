# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Fixed values of the article 2 protocol (docs/02-protocol.md).

Method parameters stay next to their method (W1/SS in waveform.py). This module
holds what the runner, CLI and evaluation must agree on.
"""

import re

CONDITIONS = ("b0", "b1", "w1", "ss")

# Evaluation: reported only. Development: used to choose configurations.
EVALUATION_MACHINES = (
    "BlowerDustCollector",
    "Sander",
    "SewingMachine",
    "ToothBrush",
    "ToyDrone",
)
DEVELOPMENT_MACHINES = (
    "ToyCar",
    "ToyCarEmu",
    "bearingEmu",
    "fan",
    "gearboxEmu",
    "sliderEmu",
    "valveEmu",
)
# Dev5 is a diagnostic subset without the ToyCar family.
DEV5_EXCLUDED = ("ToyCar", "ToyCarEmu")
DATASET_MACHINES = {"eval": EVALUATION_MACHINES, "dev": DEVELOPMENT_MACHINES}
MACHINES = EVALUATION_MACHINES

# Normal training memory and test clips per machine, the same in both datasets.
TRAIN_CLIPS = 1000
SOURCE_TRAIN_CLIPS = 990
TARGET_TRAIN_CLIPS = 10
TEST_CLIPS = 200
# Evaluation test clips are anonymous; Development names carry domain and label.
TEST_FILENAMES = frozenset(f"section_00_{i:04d}.wav" for i in range(TEST_CLIPS))
DEV_TEST_FILENAME = re.compile(
    r"section_00_(?P<domain>source|target)_test_(?P<label>normal|anomaly)_\d{4}_.+\.wav"
)
PAUC_MAX_FPR = 0.1

# Detector shared by every condition.
CHECKPOINT_SHA256 = "8d1b234032a9ccff353612dc6c20982346dc2968b205b79d97303eb5e77bfb34"
RDP_GAMMA = 4
VARMIN_K = 4
THRESHOLD_QUANTILE = 0.9

EVALUATOR_REVISION = "f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75"
