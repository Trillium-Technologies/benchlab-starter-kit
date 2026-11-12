#!/usr/bin/env python3
"""Scores collections of past forecasts with the competition's own scoring
code (swp_scoring/, an unmodified copy of what scores the leaderboard).

    python3 score.py                       # the demo: reproduces expected_report.json
    python3 score.py data/forecasts/persistence.json my_model.json \\
        --start 2026-07-01T00:00:00Z --end 2026-09-27T18:00:00Z -o report.json

Each forecast file is {"name": ..., "forecasts": {cycle_ts: forecast.json
object}}, where cycle_ts is the platform's t0 form ("20260701T060000Z") and
the object is exactly what a submission uploads. See README.md.

The evaluation grid is every scheduled cycle in [--start, --end], whatever
the files contain. A cycle missing from a file, and any invalid value in
one, is filled with persistence -- the same rule the platform applies.
"""

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# pylint: disable=wrong-import-position
from swp_scoring.core.evaluate import (  # noqa: E402
    build_grid,
    observation_window,
    score_baselines,
    score_forecasts,
)
from swp_scoring.core.grid import parse_forecast  # noqa: E402
from swp_scoring.core.types import (  # noqa: E402
    CONFIG_DIR,
    format_valid_time,
    load_competition_contract,
    parse_cycle_ts,
    parse_valid_time,
)
from swp_scoring.sources.ace_archive import (  # noqa: E402
    fetch_month,
    month_url,
    months_between,
    parse,
)

DATA = HERE / "data"
DECIMALS = 6  # rounding in the report, so it diffs cleanly across numpy versions


def load_observations(start, end, archive_dir: Path | None, contract):
    """{valid_time: speed}, valid rows only, from the local archive copies
    (or NASA when archive_dir is None)."""
    lo, hi = format_valid_time(start), format_valid_time(end)
    observations = {}
    for yyyymm in months_between(start, end):
        if archive_dir is None:
            rows = fetch_month(yyyymm)
        else:
            path = archive_dir / Path(month_url(yyyymm)).name
            if not path.exists():
                sys.exit(
                    f"missing {path}: this window needs archive month "
                    f"{yyyymm}. Use --live to fetch it from NASA."
                )
            rows = parse(path.read_text(encoding="ascii", errors="replace"))
        for row in rows:
            if lo <= row.valid_time <= hi and row.is_valid(contract):
                observations[row.valid_time] = row.speed
    return observations


def load_forecasts(path: Path, grid, contract):
    """(name, {t0: 72 floats, NaN where missing/invalid}, coverage)."""
    doc = json.loads(path.read_text())
    in_grid = set(grid.cycles)
    forecasts, outside = {}, 0
    for cycle_ts, body in doc["forecasts"].items():
        t0 = parse_cycle_ts(cycle_ts)
        if t0 in in_grid:
            forecasts[t0] = parse_forecast(body, contract)
        else:
            outside += 1
    n_values = len(grid.cycles) * contract.horizon_hours
    valid = int(sum(np.isfinite(f).sum() for f in forecasts.values()))
    coverage = {
        "cycles_in_grid": len(grid.cycles),
        "cycles_submitted": len(forecasts),
        "cycles_outside_grid_ignored": outside,
        "values_valid": valid,
        "values_persistence_filled": n_values - valid,
    }
    return doc.get("name", path.stem), forecasts, coverage


def json_safe(value):
    """NaN -> null (JSON has no NaN), floats rounded."""
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, DECIMALS)
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    return value


def print_table(scores: dict, coverage: dict) -> None:
    head = ("", "S_final", "RMSE", "TRMSE", "bias", "S_49:72", "filled")
    print(f"{head[0]:<28}" + "".join(f"{h:>10}" for h in head[1:]))
    rows = sorted(scores.items(), key=lambda kv: kv[1]["s_final"])
    for name, r in rows:
        cov = coverage.get(name)
        filled = (
            f"{cov['values_persistence_filled'] / (cov['cycles_in_grid'] * 72):.0%}"
            if cov
            else "-"
        )
        print(
            f"{name:<28}{r['s_final']:>10.2f}{r['mean_rmse']:>10.2f}"
            f"{r['mean_trmse']:>10.2f}{r['mean_bias']:>10.2f}"
            f"{r['s_49_72']:>10.2f}{filled:>10}"
        )


def main() -> int:
    window = json.loads((DATA / "window.json").read_text())
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    ap.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="forecast files (default: data/forecasts/*.json)",
    )
    ap.add_argument("--start", default=window["start"], help="first cycle")
    ap.add_argument("--end", default=window["end"], help="last cycle")
    ap.add_argument("--archive-dir", type=Path, default=DATA / "ace")
    ap.add_argument(
        "--live",
        action="store_true",
        help="fetch ground truth from NASA instead of --archive-dir",
    )
    ap.add_argument(
        "--official-baselines",
        action="store_true",
        help="also score the baselines computed inside the scorer, the "
        "way the leaderboard does",
    )
    ap.add_argument("-o", "--output", type=Path, default=Path("report.json"))
    args = ap.parse_args()
    files = args.files or sorted((DATA / "forecasts").glob("*.json"))

    contract = load_competition_contract()
    start, end = parse_valid_time(args.start), parse_valid_time(args.end)
    obs_start, obs_end = observation_window(start, end, contract)
    observations = load_observations(
        obs_start, obs_end, None if args.live else args.archive_dir, contract
    )
    grid = build_grid(observations, start, end, contract)

    scores, coverage = {}, {}
    try:
        for path in files:
            name, forecasts, cov = load_forecasts(path, grid, contract)
            scores[name] = asdict(score_forecasts(grid, forecasts, contract))
            coverage[name] = cov
        if args.official_baselines:
            for name, report in score_baselines(grid, contract).items():
                scores[f"official:{name}"] = asdict(report)
    except ValueError as e:
        # metric.lead_score: no valid observation within the persistence
        # look-back before some cycle, so a missing value can't be filled.
        sys.exit(f"cannot score this window: {e}")

    report = {
        "meta": {
            "start": format_valid_time(start),
            "end": format_valid_time(end),
            "n_cycles": len(grid.cycles),
            "horizon_hours": contract.horizon_hours,
            "ground_truth": "live" if args.live else "archive snapshot",
            "n_valid_observations": len(observations),
            "contract_sha256": hashlib.sha256(
                (CONFIG_DIR / "competition.toml").read_bytes()
            ).hexdigest(),
        },
        "coverage": coverage,
        "scores": scores,
    }
    report = json_safe(report)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    print(
        f"{report['meta']['n_cycles']} cycles, "
        f"{args.start} .. {args.end}  (lower is better, km/s)\n"
    )
    print_table(report["scores"], coverage)
    print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
