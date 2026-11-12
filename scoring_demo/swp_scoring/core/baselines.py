"""The three official baseline models (spec section 10). Each returns a
pred[N, H] matrix over the same grid a submission is scored on, so baselines
go through exactly the same scoring code as participants."""

from datetime import datetime, timedelta

import numpy as np

from .grid import HOUR
from .types import format_valid_time

RECURRENCE_PERIOD = timedelta(days=27)


def persistence(persistence_vec: np.ndarray, horizon: int) -> np.ndarray:
    """v_hat(t0, tau) = v_latest(t0) for every tau."""
    return np.repeat(persistence_vec[:, None], horizon, axis=1)


def recurrence_27(
    cycles: list[datetime],
    observations: dict[str, float],
    persistence_vec: np.ndarray,
    horizon: int,
) -> np.ndarray:
    """v_hat(t0, tau) = v(t0 + tau - 27 days), falling back to persistence
    where that historical observation is missing. Uses only data from
    before t0, since tau <= horizon < 27 days."""
    if horizon * HOUR >= RECURRENCE_PERIOD:
        raise ValueError("recurrence would read observations after t0")
    out = np.repeat(persistence_vec[:, None], horizon, axis=1)
    for i, t0 in enumerate(cycles):
        for tau in range(1, horizon + 1):
            key = format_valid_time(t0 + tau * HOUR - RECURRENCE_PERIOD)
            value = observations.get(key)
            if value is not None:
                out[i, tau - 1] = value
    return out


def climatology(n_cycles: int, horizon: int, value: float) -> np.ndarray:
    """A constant forecast, fixed before the competition from historical data."""
    if not np.isfinite(value):
        raise ValueError(
            "climatology_kms is not set in config/competition.toml -- run "
            "python3 -m scoring.scripts.compute_climatology and record the result"
        )
    return np.full((n_cycles, horizon), value)
