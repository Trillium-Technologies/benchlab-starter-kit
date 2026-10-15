"""The evaluation grid: which (t0, tau) pairs exist, what was observed for
each, and what each submission predicted, with persistence filling the gaps.

Rows are every scheduled cycle t0 from competition start (spec: "the full
competition period"), the same for every team; columns are lead times
tau = 1..H. Observations are keyed by valid_time string
(core.types.format_valid_time) and contain only VALID values -- anything
absent is a missing observation (NaN), excluded from scoring for everyone
alike (spec section 3).
"""

from datetime import datetime, timedelta

import numpy as np

from .types import CompetitionContract, format_valid_time

HOUR = timedelta(hours=1)


def scheduled_cycles(
    start: datetime, end: datetime, cycle_hours_utc: tuple[int, ...]
) -> list[datetime]:
    """Every scheduled cycle time in [start, end], ascending."""
    t = start.replace(minute=0, second=0, microsecond=0)
    if t < start:
        t += HOUR
    cycles = []
    while t <= end:
        if t.hour in cycle_hours_utc:
            cycles.append(t)
        t += HOUR
    return cycles


def observed_matrix(
    cycles: list[datetime], observations: dict[str, float], horizon: int
) -> np.ndarray:
    """obs[i, tau-1] = v(t0_i + tau), or NaN when there's no valid observation."""
    out = np.full((len(cycles), horizon), np.nan)
    for i, t0 in enumerate(cycles):
        for tau in range(1, horizon + 1):
            value = observations.get(format_valid_time(t0 + tau * HOUR))
            if value is not None:
                out[i, tau - 1] = value
    return out


def persistence_vector(
    cycles: list[datetime], observations: dict[str, float], lookback_hours: int
) -> np.ndarray:
    """v_latest(t0) for each cycle: the most recent valid observation at or
    before t0 -- never after it (spec section 4). NaN when none exists
    within lookback_hours; metric.lead_score then refuses to score a row
    that needs it, rather than dropping the pair."""
    out = np.full(len(cycles), np.nan)
    for i, t0 in enumerate(cycles):
        for back in range(lookback_hours + 1):
            value = observations.get(format_valid_time(t0 - back * HOUR))
            if value is not None:
                out[i] = value
                break
    return out


def parse_forecast(body, contract: CompetitionContract) -> np.ndarray:
    """A forecast.json body -> H floats, NaN wherever a prediction is
    missing: null, NaN, non-numeric, outside contract.valid_range, or the
    whole body malformed (wrong shape, missing field). Never raises -- a bad
    value is a missing prediction, which persistence fills.

    The body's own "t0" field is not checked: the S3 key the platform wrote
    it under already identifies the cycle authoritatively."""
    out = np.full(contract.horizon_hours, np.nan)
    try:
        values = body[contract.forecast_field]
    except (TypeError, KeyError):
        return out
    if not isinstance(values, list) or len(values) != contract.horizon_hours:
        return out
    lo, hi = contract.valid_range
    for i, raw in enumerate(values):
        if raw is None or isinstance(raw, bool):
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            continue
        if np.isfinite(v) and lo <= v <= hi:
            out[i] = v
    return out


def prediction_matrix(
    cycles: list[datetime],
    forecasts: dict[datetime, np.ndarray],
    persistence: np.ndarray,
    horizon: int,
) -> np.ndarray:
    """pred[i, :] starts as persistence for cycle i, then every valid
    submitted value overwrites it. A cycle with no forecast at all (any
    failed run, or no run) stays entirely persistence."""
    out = np.repeat(persistence[:, None], horizon, axis=1)
    for i, t0 in enumerate(cycles):
        submitted = forecasts.get(t0)
        if submitted is None:
            continue
        valid = np.isfinite(submitted)
        out[i, valid] = submitted[valid]
    return out
