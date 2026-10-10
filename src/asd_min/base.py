"""ASDKit backend interface: fit on normal training data, then score queries."""

import logging
from abc import ABC, abstractmethod
from typing import Dict

import numpy as np

logger = logging.getLogger(__name__)


class BaseBackend(ABC):
    """Abstract ASDKit backend.

    Both methods take feature dictionaries keyed by name (for example
    ``"embed_freq"``, ``"path"``, ``"section"``, ``"is_normal"``), so a backend
    reads only the entries it needs.
    """

    @abstractmethod
    def fit(self, train_dict: dict) -> None:
        """Build the backend's normal reference from training features.

        Args:
            train_dict: Feature arrays of the normal training clips, one row per clip.
        """
        pass

    @abstractmethod
    def anomaly_score(self, test_dict: dict) -> Dict[str, np.ndarray]:
        """Score query clips; larger means more anomalous.

        Args:
            test_dict: Feature arrays of the query clips, one row per clip.

        Returns:
            Score arrays of shape ``[N]`` keyed by name. ``"main"`` is the score
            written to the submission CSV; other keys are diagnostics.
        """
        pass

    def check_target(self, is_target: np.ndarray) -> None:
        """Warn when no target-domain clip is present.

        Args:
            is_target: ``[N]`` flags, nonzero for target-domain clips.
        """
        if np.sum(is_target) == 0:
            logger.warning("number of target data is 0.")
