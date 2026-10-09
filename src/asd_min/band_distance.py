"""Band-wise scaled cosine distance shared by BEAM and VarMin."""

import math
from typing import Iterator, Tuple

import numpy as np


def _validate_band_embeddings(name: str, embeddings: np.ndarray) -> np.ndarray:
    array = np.asarray(embeddings)
    if array.ndim != 3:
        raise ValueError(f"{name} must have shape [N, F, D], got {array.shape}")
    if not np.issubdtype(array.dtype, np.floating):
        raise TypeError(f"{name} must have a floating dtype, got {array.dtype}")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains NaN or Inf")
    return array.astype(np.float32, copy=False)


def _iter_slices(length: int, chunk_size: int):
    for start in range(0, length, chunk_size):
        yield slice(start, min(start + chunk_size, length))


def l2_normalize(embeddings: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """L2-normalize the last axis, mapping near-zero vectors safely to zero."""
    if not math.isfinite(eps) or eps <= 0:
        raise ValueError(f"eps must be finite and positive, got {eps}")
    array = np.asarray(embeddings)
    if not np.issubdtype(array.dtype, np.floating):
        raise TypeError(f"embeddings must have a floating dtype, got {array.dtype}")
    if not np.isfinite(array).all():
        raise ValueError("embeddings contains NaN or Inf")
    norm = np.linalg.norm(array, axis=-1, keepdims=True)
    return np.divide(array, norm, out=np.zeros_like(array), where=norm > eps)


def cosine_distance(
    query: np.ndarray, reference: np.ndarray, eps: float = 1e-12
) -> np.ndarray:
    """Calculate exact ``0.5 * (1 - cosine)`` pairwise band distances.

    Two-dimensional inputs ``[N, D]`` produce ``[Q, R]``. Three-dimensional
    inputs ``[N, F, D]`` produce ``[Q, R, F]`` and compare aligned bands only.
    Cosine similarity involving a near-zero vector is defined as zero.
    """
    query_array = np.asarray(query)
    reference_array = np.asarray(reference)
    squeeze_band = query_array.ndim == reference_array.ndim == 2
    if squeeze_band:
        query_array = query_array[:, None, :]
        reference_array = reference_array[:, None, :]
    if query_array.ndim != 3 or reference_array.ndim != 3:
        raise ValueError("query and reference must both be [N, D] or [N, F, D]")
    if query_array.shape[1:] != reference_array.shape[1:]:
        raise ValueError(
            "query and reference band shapes differ: "
            f"{query_array.shape[1:]} != {reference_array.shape[1:]}"
        )
    query_norm = l2_normalize(query_array, eps=eps)
    reference_norm = l2_normalize(reference_array, eps=eps)
    similarity = np.einsum("qfd,rfd->qrf", query_norm, reference_norm)
    distance = 0.5 * (1.0 - np.clip(similarity, -1.0, 1.0))
    return distance[:, :, 0] if squeeze_band else distance


def _cosine_distance_normalized(
    query_normalized: np.ndarray, reference_normalized: np.ndarray
) -> np.ndarray:
    """D(q[f], y[i,f]) = 0.5 * (1 - cosine) for L2-normalized inputs, [Q, R, F]."""
    similarity = np.einsum(
        "qfd,rfd->qrf", query_normalized, reference_normalized, optimize=True
    )
    return 0.5 * (1.0 - np.clip(similarity, -1.0, 1.0))


def self_excluded_distances(
    reference_normalized: np.ndarray, chunk_size: int
) -> Iterator[Tuple[slice, np.ndarray]]:
    """Yield reference-to-reference distances in chunks, with D(y[z], y[z]) = inf."""
    for query_slice in _iter_slices(len(reference_normalized), chunk_size):
        distance = _cosine_distance_normalized(
            reference_normalized[query_slice], reference_normalized
        )
        global_indices = np.arange(query_slice.start, query_slice.stop)
        distance[np.arange(len(global_indices)), global_indices, :] = np.inf
        yield query_slice, distance


def nearest_reference(distance: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return argmin_i and min_i of ``[Q, R, F]`` distances, each ``[Q, F]``."""
    index = distance.argmin(axis=1)
    value = np.take_along_axis(distance, index[:, None, :], axis=1)[:, 0, :]
    return index, value
