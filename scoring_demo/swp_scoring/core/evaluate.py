"""End-to-end evaluation over the competition grid -- the single path every
caller (the score_submissions Lambda, canary/eval_canary.py,
scoring/baseline/compare_baselines.py) uses, so participants and baselines
are scored identically."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

from . import baselines
from .grid import (
    observed_matrix,
    persistence_vector,
    prediction_matrix,
    scheduled_cycles,
)
from .metric import ScoreReport, score
from .types import CompetitionContract

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvaluationGrid:
    cycles: list[datetime]
    observations: dict[str, float]  # valid observations only, by valid_time
    obs: np.ndarray  # [N, H]
    persistence: np.ndarray  # [N]


def observation_window(
    start: datetime, end: datetime, contract: CompetitionContract
) -> tuple[datetime, datetime]:
    """The span of observations a grid over [start, end] can touch: back far
    enough for persistence and 27-day recurrence, forward to the last
    cycle's last lead time."""
    back = baselines.RECURRENCE_PERIOD + timedelta(
        hours=contract.persistence_lookback_hours
    )
    return start - back, end + timedelta(hours=contract.horizon_hours)


def build_grid(
    observations: dict[str, float],
    start: datetime,
    end: datetime,
    contract: CompetitionContract,
) -> EvaluationGrid:
    cycles = scheduled_cycles(start, end, contract.cycle_hours_utc)
    return EvaluationGrid(
        cycles=cycles,
        observations=observations,
        obs=observed_matrix(cycles, observations, contract.horizon_hours),
        persistence=persistence_vector(
            cycles, observations, contract.persistence_lookback_hours
        ),
    )


def _score(
    grid: EvaluationGrid, pred: np.ndarray, contract: CompetitionContract
) -> ScoreReport:
    return score(
        grid.obs, pred, contract.percentile_intervals, contract.quantile_method
    )


def score_forecasts(
    grid: EvaluationGrid,
    forecasts: dict[datetime, np.ndarray],
    contract: CompetitionContract,
) -> ScoreReport:
    """forecasts: {cycle t0: H floats from grid.parse_forecast}. Cycles
    missing from `forecasts`, and any NaN within one, are persistence-filled.
    """
    pred = prediction_matrix(
        grid.cycles, forecasts, grid.persistence, contract.horizon_hours
    )
    return _score(grid, pred, contract)


def baseline_predictions(
    grid: EvaluationGrid, contract: CompetitionContract
) -> dict[str, np.ndarray]:
    """The official baselines' pred[N, H] matrices. Climatology is skipped
    (with a warning) until its constant is recorded in config, rather than
    failing the whole run."""
    horizon = contract.horizon_hours
    preds = {
        "persistence": baselines.persistence(grid.persistence, horizon),
        "recurrence_27d": baselines.recurrence_27(
            grid.cycles, grid.observations, grid.persistence, horizon
        ),
    }
    if np.isfinite(contract.climatology_kms):
        preds["climatology"] = baselines.climatology(
            len(grid.cycles), horizon, contract.climatology_kms
        )
    else:
        log.warning(
            "climatology baseline skipped: climatology_kms not set in config"
        )
    return preds


def score_baselines(
    grid: EvaluationGrid, contract: CompetitionContract
) -> dict[str, ScoreReport]:
    """The official baselines, scored exactly like a submission."""
    return {
        name: _score(grid, pred, contract)
        for name, pred in baseline_predictions(grid, contract).items()
    }
