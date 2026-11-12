"""The official competition metric -- assets/TIMSE_implementation.pdf.

Scoring operates on two matrices over the evaluation grid (see grid.py):
obs[N, H] and pred[N, H], row i = forecast cycle t0_i, column tau-1 = lead
time tau. Each lead time is scored independently on its own column:

    RMSE_tau  = sqrt(mean((v - v_hat)^2))                       over A_tau
    TIMSE_tau = 1/(v_max - v_min) * sum_{k=0}^{K-1} (q_{k+1} - q_k) * M_k
    TRMSE_tau = sqrt(TIMSE_tau)
    S_tau     = sqrt(RMSE_tau * TRMSE_tau)

where A_tau is the set of rows whose observation is valid, q_k are K+1
empirical quantiles of that lead's own valid observations, and M_k is the
MSE over observations >= q_k. The ranking score is the equal-weight mean of
S_tau over lead times -- never a pool across lead times, never an average
of per-forecast-window scores.
"""

from dataclasses import dataclass

import numpy as np


def rmse(observed: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((observed - predicted) ** 2)))


def timse_percentile(
    observed: np.ndarray,
    predicted: np.ndarray,
    intervals: int = 100,
    method: str = "linear",
) -> float:
    """Percentile TIMSE for ONE lead time's valid pairs (spec section 6).

    The quantile grid depends only on `observed`, never on `predicted`.
    Integration weights are the velocity widths q_{k+1} - q_k, not 1/K, and
    a zero-width interval contributes zero. If every observation is equal
    (v_max == v_min) every interval has zero width, so TIMSE is 0."""
    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if observed.shape != predicted.shape or observed.ndim != 1:
        raise ValueError(
            f"expected two equal-length 1-D arrays, got {observed.shape} and {predicted.shape}"
        )
    n = observed.size
    if n == 0:
        raise ValueError("timse_percentile() requires at least one pair")

    span = observed.max() - observed.min()
    if span == 0.0:
        return 0.0

    # `method` comes from config/competition.toml as a plain string; numpy's
    # stub only accepts its Literal names, but validates at runtime anyway.
    q = np.quantile(
        observed, np.arange(intervals + 1) / intervals, method=method  # type: ignore[call-overload]
    )
    widths = np.diff(q)

    order = np.argsort(observed, kind="stable")
    v_sorted = observed[order]
    sq_err_sorted = ((observed - predicted) ** 2)[order]
    suffix_sum = np.concatenate([np.cumsum(sq_err_sorted[::-1])[::-1], [0.0]])

    # First sorted index with v >= q_k, for each lower threshold q_0..q_{K-1}.
    first = np.searchsorted(v_sorted, q[:-1], side="left")
    n_k = n - first  # >= 1, since every q_k <= v_max
    m_k = suffix_sum[first] / n_k

    return float(np.sum(np.where(widths > 0, widths * m_k, 0.0)) / span)


@dataclass(frozen=True)
class LeadScore:
    rmse: float
    timse: float
    trmse: float
    s: float
    bias: float  # mean(predicted - observed)
    n: int


def lead_score(
    observed: np.ndarray,
    predicted: np.ndarray,
    intervals: int = 100,
    method: str = "linear",
) -> LeadScore | None:
    """Scores one lead-time column. Pairs with a NaN observation are
    excluded (spec section 3). A NaN prediction where the observation is
    valid is a bug -- grid.prediction_matrix fills those with persistence
    before scoring (spec section 4) -- so it raises rather than silently
    dropping the pair. Returns None if the column has no valid observation."""
    valid = np.isfinite(observed)
    obs, pred = observed[valid], predicted[valid]
    if obs.size == 0:
        return None
    if not np.all(np.isfinite(pred)):
        raise ValueError(
            "missing prediction where the observation is valid: either "
            "predictions weren't persistence-filled (grid.prediction_matrix), "
            "or no valid observation existed within persistence_lookback_hours "
            "before that cycle's t0"
        )
    r = rmse(obs, pred)
    t = timse_percentile(obs, pred, intervals, method)
    tr = float(np.sqrt(t))
    return LeadScore(
        rmse=r,
        timse=t,
        trmse=tr,
        s=float(np.sqrt(r * tr)),
        bias=float(np.mean(pred - obs)),
        n=int(obs.size),
    )


@dataclass(frozen=True)
class ScoreReport:
    """Everything spec section 9 asks the evaluation to retain. Curves are
    indexed by lead time (curve[tau-1]); a lead with no valid observation
    yet is NaN and is left out of every mean."""

    s_final: float
    mean_rmse: float
    mean_trmse: float
    mean_bias: float
    s_49_72: float
    n_leads: int
    s_curve: list[float]
    rmse_curve: list[float]
    trmse_curve: list[float]
    bias_curve: list[float]
    n_curve: list[int]


def _nanmean(values: list[float]) -> float:
    finite = [v for v in values if np.isfinite(v)]
    return float(np.mean(finite)) if finite else float("nan")


def score(
    observed: np.ndarray,
    predicted: np.ndarray,
    intervals: int = 100,
    method: str = "linear",
) -> ScoreReport:
    """observed, predicted: [N cycles, H lead times]. Each lead's S_tau gets
    equal weight in S_final regardless of how many valid pairs it has."""
    if observed.shape != predicted.shape or observed.ndim != 2:
        raise ValueError(
            f"expected two equal-shape [N, H] matrices, got {observed.shape} and {predicted.shape}"
        )
    horizon = observed.shape[1]
    nan = float("nan")
    s_curve, rmse_curve, trmse_curve, bias_curve, n_curve = [], [], [], [], []
    for tau in range(horizon):
        ls = lead_score(observed[:, tau], predicted[:, tau], intervals, method)
        s_curve.append(ls.s if ls else nan)
        rmse_curve.append(ls.rmse if ls else nan)
        trmse_curve.append(ls.trmse if ls else nan)
        bias_curve.append(ls.bias if ls else nan)
        n_curve.append(ls.n if ls else 0)

    return ScoreReport(
        s_final=_nanmean(s_curve),
        mean_rmse=_nanmean(rmse_curve),
        mean_trmse=_nanmean(trmse_curve),
        mean_bias=_nanmean(bias_curve),
        s_49_72=_nanmean(s_curve[48:72]),
        n_leads=sum(1 for n in n_curve if n > 0),
        s_curve=s_curve,
        rmse_curve=rmse_curve,
        trmse_curve=trmse_curve,
        bias_curve=bias_curve,
        n_curve=n_curve,
    )
