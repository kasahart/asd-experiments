"""Band-wise Equalized Anomaly Measure with variance-minimum rescaling.

Each equation in beam.md is one function: band distances in band_distance.py,
VarMin terms in varmin.py, and the BEAM minimum and band mean here. The
ASDKit backend interface and every name below stay importable from this module.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .band_distance import (  # noqa: F401  (public names kept for compatibility)
    _cosine_distance_normalized,
    _iter_slices,
    _validate_band_embeddings,
    cosine_distance,
    l2_normalize,
    nearest_reference,
)
from .base import BaseBackend
from .varmin import (  # noqa: F401  (public names kept for compatibility)
    VarianceMinRescaler,
    compute_local_density,
    estimate_train_all_alpha,
    rescaled_distance,
)

logger = logging.getLogger(__name__)


def minimum_band_scores(
    distances: np.ndarray,
    local_density: Optional[np.ndarray] = None,
    alpha: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Per-band BEAM score from precomputed distances.

    raw:     band[f] = min_i D(q[f], y[i,f])
    VarMin:  band[f] = min_i { D(q[f], y[i,f]) - alpha[f] b[i,f] }

    Args:
        distances: ``[Q, R, F]`` distances.
        local_density: ``b`` of shape ``[R, F]``, or None for the raw score.
        alpha: Per-band ``[F]`` coefficients, or None for the raw score.

    Returns:
        Band scores ``[Q, F]``.
    """
    distance = np.asarray(distances)
    if distance.ndim != 3:
        raise ValueError(f"distances must have shape [Q, R, F], got {distance.shape}")
    if (local_density is None) != (alpha is None):
        raise ValueError(
            "local_density and alpha must either both be set or both be None"
        )
    if local_density is None:
        return distance.min(axis=1)
    density = np.asarray(local_density)
    alpha_array = np.asarray(alpha)
    if density.shape != distance.shape[1:]:
        raise ValueError(
            f"local_density must have shape {distance.shape[1:]}, got {density.shape}"
        )
    if alpha_array.shape != (distance.shape[2],):
        raise ValueError(
            f"alpha must have shape {(distance.shape[2],)}, got {alpha_array.shape}"
        )
    return rescaled_distance(distance, alpha_array, density).min(axis=1)


def band_mean(band_scores: np.ndarray) -> np.ndarray:
    """score = uniform mean over frequency bands.

    Args:
        band_scores: ``[Q, F]`` band scores.

    Returns:
        Clip scores ``[Q]``.
    """
    return band_scores.mean(axis=1)


@dataclass
class _BandMemory:
    """Normal memory of one section.

    Attributes:
        embeddings: ``[R, F, D]`` L2-normalized normal references ``y``.
        paths: ``[R]`` reference filenames for self-match exclusion, or None.
        local_density: ``b`` of shape ``[R, F]`` (zeros without rescaling).
        alpha: Per-band ``[F]`` coefficients (zeros without rescaling).
    """

    embeddings: np.ndarray
    paths: Optional[np.ndarray]
    local_density: np.ndarray
    alpha: np.ndarray


class BEAMVarianceMin(BaseBackend):
    """BEAM backend with optional per-band variance-minimum score rescaling.

    The canonical reproduction assumes TrainAll leave-one-out calibration and a
    separate alpha for each frequency band, applies rescaling before the uniform
    frequency mean, and minimizes the adjusted distance over all references. The
    available paper description does not fully disambiguate the per-band scope,
    so this is an explicit reproduction assumption rather than a paper-guaranteed
    detail.

    Args:
        embed_key: Feature dictionary key holding ``[N, F, D]`` band features.
        sep_section: Build one memory per ``"section"`` value instead of one
            shared memory.
        use_rescaling: Apply VarMin; False gives raw BEAM scores as ``"main"``.
        rescale_k: VarMin neighbour count K.
        rescale_validation: VarMin validation; only ``"train_all"``.
        rescale_scope: VarMin alpha scope; only ``"per_band"``.
        chunk_size: Number of queries compared at once.
        eps: Norm and variance threshold.
    """

    diagnostic_score_keys = {"raw", "rescale_delta"}

    def __init__(
        self,
        embed_key: str = "embed_freq",
        sep_section: bool = False,
        use_rescaling: bool = True,
        rescale_k: int = 4,
        rescale_validation: str = "train_all",
        rescale_scope: str = "per_band",
        chunk_size: int = 128,
        eps: float = 1e-12,
    ):
        if (
            isinstance(chunk_size, bool)
            or not isinstance(chunk_size, int)
            or chunk_size <= 0
        ):
            raise ValueError(
                f"chunk_size must be a positive integer, got {chunk_size!r}"
            )
        if not math.isfinite(eps) or eps <= 0:
            raise ValueError(f"eps must be finite and positive, got {eps}")
        self.embed_key = embed_key
        self.sep_section = sep_section
        self.use_rescaling = use_rescaling
        self.chunk_size = chunk_size
        self.eps = eps
        self.rescaler = VarianceMinRescaler(
            k=rescale_k,
            validation=rescale_validation,
            scope=rescale_scope,
            chunk_size=chunk_size,
            eps=eps,
        )
        self.memory: Dict[Any, _BandMemory] = {}
        self.band_shape: Optional[Tuple[int, int]] = None

    def _get_sections(self, extract_dict: dict, length: int) -> np.ndarray:
        """Section id per clip; all zeros when sections are not separated."""
        if "section" not in extract_dict:
            if self.sep_section:
                raise KeyError("section is required when sep_section=True")
            return np.zeros(length, dtype=np.int64)
        section = np.asarray(extract_dict["section"])
        if section.shape != (length,):
            raise ValueError(f"section must have shape [{length}], got {section.shape}")
        return section if self.sep_section else np.zeros_like(section)

    @staticmethod
    def _get_paths(extract_dict: dict, length: int) -> Optional[np.ndarray]:
        """Filenames per clip used to exclude self matches, or None if absent."""
        if "path" not in extract_dict:
            return None
        paths = np.asarray(extract_dict["path"])
        if paths.shape != (length,):
            raise ValueError(f"path must have shape [{length}], got {paths.shape}")
        return paths

    def fit(self, train_dict: dict) -> None:
        """Build the normal memory (and VarMin terms) for each section.

        Clips with ``is_normal != 1`` are skipped when ``"is_normal"`` is given.

        Args:
            train_dict: ``embed_key`` features ``[N, F, D]`` and optionally
                ``"path"``, ``"section"`` and ``"is_normal"`` arrays of length N.
        """
        embeddings = _validate_band_embeddings(
            self.embed_key, train_dict[self.embed_key]
        )
        length, frequency_count, dimension = embeddings.shape
        self.band_shape = (frequency_count, dimension)
        sections = self._get_sections(train_dict, length)
        paths = self._get_paths(train_dict, length)
        if paths is None:
            logger.warning(
                "Training paths are unavailable; path-based self-match exclusion "
                "will not be possible in anomaly_score()."
            )
        if "is_normal" in train_dict:
            is_normal = np.asarray(train_dict["is_normal"])
            if is_normal.shape != (length,):
                raise ValueError(
                    f"is_normal must have shape [{length}], got {is_normal.shape}"
                )
            normal = is_normal == 1
        else:
            normal = np.ones(length, dtype=bool)

        self.memory.clear()
        for section_value in np.unique(sections):
            selected = (sections == section_value) & normal
            if not selected.any():
                raise ValueError(
                    f"No normal references are available for section {section_value!r}"
                )
            reference = l2_normalize(embeddings[selected], eps=self.eps)
            if self.use_rescaling:
                local_density, alpha = self.rescaler.fit(reference)
            else:
                local_density = np.zeros(reference.shape[:2], dtype=np.float32)
                alpha = np.zeros(reference.shape[1], dtype=np.float32)
            self.memory[section_value] = _BandMemory(
                embeddings=reference,
                paths=None if paths is None else paths[selected],
                local_density=local_density,
                alpha=alpha,
            )

    def _score_section(
        self,
        query: np.ndarray,
        query_paths: Optional[np.ndarray],
        memory: _BandMemory,
    ) -> Dict[str, np.ndarray]:
        """Band scores and selected references for queries of one section.

        A query whose path equals a reference path skips that reference, so
        rescoring the training clips is leave-one-out.

        Args:
            query: ``[Q, F, D]`` query features.
            query_paths: ``[Q]`` query filenames, or None.
            memory: Fitted memory of the section.

        Returns:
            The dictionary described in ``anomaly_score_details``, for these queries.
        """
        query_normalized = l2_normalize(query, eps=self.eps)
        query_count, frequency_count, _ = query.shape
        raw_band = np.empty((query_count, frequency_count), dtype=np.float32)
        main_band = np.empty_like(raw_band)
        raw_reference_index = np.empty((query_count, frequency_count), dtype=np.intp)
        main_reference_index = np.empty_like(raw_reference_index)
        if query_paths is not None and memory.paths is None:
            logger.warning(
                "Reference paths are unavailable; self matches cannot be excluded."
            )
        if query_paths is None:
            logger.warning(
                "Query paths are unavailable; self matches cannot be excluded."
            )

        for query_slice in _iter_slices(query_count, self.chunk_size):
            distance = _cosine_distance_normalized(
                query_normalized[query_slice], memory.embeddings
            )
            if query_paths is not None and memory.paths is not None:
                self_match = query_paths[query_slice, None] == memory.paths[None, :]
                distance = np.where(self_match[:, :, None], np.inf, distance)
            if np.isinf(distance).all(axis=1).any():
                raise ValueError(
                    "Self-match exclusion removed every reference for at least one query"
                )
            raw_index, raw_value = nearest_reference(distance)
            raw_reference_index[query_slice] = raw_index
            raw_band[query_slice] = raw_value
            if self.use_rescaling:
                main_index, main_value = nearest_reference(
                    rescaled_distance(distance, memory.alpha, memory.local_density)
                )
                main_reference_index[query_slice] = main_index
                main_band[query_slice] = main_value
            else:
                main_band[query_slice] = raw_band[query_slice]
                main_reference_index[query_slice] = raw_index

        if not np.isfinite(raw_band).all() or not np.isfinite(main_band).all():
            raise FloatingPointError("BEAM scoring produced NaN or Inf")

        bands = np.arange(frequency_count)[None, :]
        raw_reference_embedding = memory.embeddings[raw_reference_index, bands, :]
        main_reference_embedding = memory.embeddings[main_reference_index, bands, :]
        raw_selected_density = memory.local_density[raw_reference_index, bands]
        main_selected_density = memory.local_density[main_reference_index, bands]
        alpha = np.broadcast_to(memory.alpha, (query_count, frequency_count)).copy()

        return {
            "main": main_band,
            "raw": raw_band,
            "rescale_delta": raw_band - main_band,
            "main_reference_index": main_reference_index,
            "raw_reference_index": raw_reference_index,
            "main_reference_embedding": main_reference_embedding,
            "raw_reference_embedding": raw_reference_embedding,
            "main_selected_density": main_selected_density,
            "raw_selected_density": raw_selected_density,
            "alpha": alpha,
        }

    def anomaly_score_details(self, test_dict: dict) -> Dict[str, np.ndarray]:
        """Return band-level BEAM scores and their selected references.

        Reference indices are local to the fitted memory for each query's section.
        Reference embeddings are the L2-normalized values stored in that memory.

        Args:
            test_dict: ``embed_key`` features ``[N, F, D]`` and optionally
                ``"path"`` and ``"section"``.

        Returns:
            Arrays keyed by name (``N`` queries, ``F`` bands, ``D`` dimensions):

            - ``main``, ``raw``, ``rescale_delta``: ``[N, F]`` VarMin band scores,
              raw band scores, and their difference ``raw - main``.
            - ``main_reference_index``, ``raw_reference_index``: ``[N, F]`` reference
              chosen per band with and without VarMin.
            - ``main_reference_embedding``, ``raw_reference_embedding``:
              ``[N, F, D]`` features of those references.
            - ``main_selected_density``, ``raw_selected_density``: ``[N, F]`` local
              density ``b`` of those references.
            - ``alpha``: ``[N, F]`` alpha of each query's section.
        """
        if not self.memory or self.band_shape is None:
            raise RuntimeError("fit() must be called before anomaly_score_details()")
        embeddings = _validate_band_embeddings(
            self.embed_key, test_dict[self.embed_key]
        )
        length = len(embeddings)
        if embeddings.shape[1:] != self.band_shape:
            raise ValueError(
                f"Expected band shape {self.band_shape}, got {embeddings.shape[1:]}"
            )
        sections = self._get_sections(test_dict, length)
        paths = self._get_paths(test_dict, length)
        frequency_count, dimension = self.band_shape
        details = {
            "main": np.empty((length, frequency_count), dtype=np.float32),
            "raw": np.empty((length, frequency_count), dtype=np.float32),
            "rescale_delta": np.empty((length, frequency_count), dtype=np.float32),
            "main_reference_index": np.empty((length, frequency_count), dtype=np.intp),
            "raw_reference_index": np.empty((length, frequency_count), dtype=np.intp),
            "main_reference_embedding": np.empty(
                (length, frequency_count, dimension), dtype=np.float32
            ),
            "raw_reference_embedding": np.empty(
                (length, frequency_count, dimension), dtype=np.float32
            ),
            "main_selected_density": np.empty(
                (length, frequency_count), dtype=np.float32
            ),
            "raw_selected_density": np.empty(
                (length, frequency_count), dtype=np.float32
            ),
            "alpha": np.empty((length, frequency_count), dtype=np.float32),
        }

        for section_value in np.unique(sections):
            if section_value not in self.memory:
                raise KeyError(f"No fitted memory for section {section_value!r}")
            selected = sections == section_value
            section_details = self._score_section(
                embeddings[selected],
                None if paths is None else paths[selected],
                self.memory[section_value],
            )
            for key, value in section_details.items():
                details[key][selected] = value

        return details

    def anomaly_score(self, test_dict: dict) -> Dict[str, np.ndarray]:
        """Clip-level anomaly scores: the band mean of ``anomaly_score_details``.

        Args:
            test_dict: Same as ``anomaly_score_details``.

        Returns:
            ``[N]`` arrays: ``main`` (VarMin score written to the CSV), ``raw``
            (BEAM without VarMin) and ``rescale_delta`` (``raw - main``).
        """
        if not self.memory or self.band_shape is None:
            raise RuntimeError("fit() must be called before anomaly_score()")
        details = self.anomaly_score_details(test_dict)
        main_score = band_mean(details["main"])
        raw_score = band_mean(details["raw"])

        return {
            "main": main_score,
            "raw": raw_score,
            "rescale_delta": raw_score - main_score,
        }
