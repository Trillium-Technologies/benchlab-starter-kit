"""The competition.toml loader and timestamp helpers shared by the scoring
engine."""

import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass(frozen=True)
class CompetitionContract:
    forecast_field: str
    horizon_hours: int
    units: str
    valid_range: tuple[float, float]
    competition_start: datetime
    cycle_hours_utc: tuple[int, ...]
    percentile_intervals: int
    quantile_method: str
    accepted_status: tuple[int, ...]
    missing_sentinel: float
    persistence_lookback_hours: int
    climatology_kms: float


def load_competition_contract(path: Path | None = None) -> CompetitionContract:
    path = path or (CONFIG_DIR / "competition.toml")
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    lo, hi = cfg["valid_range"]
    return CompetitionContract(
        forecast_field=cfg["forecast_field"],
        horizon_hours=int(cfg["horizon_hours"]),
        units=cfg["units"],
        valid_range=(float(lo), float(hi)),
        competition_start=parse_valid_time(cfg["competition_start"]),
        cycle_hours_utc=tuple(int(h) for h in cfg["cycle_hours_utc"]),
        percentile_intervals=int(cfg["percentile_intervals"]),
        quantile_method=cfg["quantile_method"],
        accepted_status=tuple(int(s) for s in cfg["accepted_status"]),
        missing_sentinel=float(cfg["missing_sentinel"]),
        persistence_lookback_hours=int(cfg["persistence_lookback_hours"]),
        climatology_kms=float(cfg["baselines"]["climatology_kms"]),
    )


def parse_cycle_ts(cycle_ts: str) -> datetime:
    """ "YYYYMMDDTHHMMSSZ" -> aware UTC datetime, the format used throughout
    aws_dev (runs.cycle_ts, S3 key prefixes, forecast.json's own "t0")."""
    return datetime.strptime(cycle_ts, "%Y%m%dT%H%M%SZ").replace(
        tzinfo=timezone.utc
    )


def format_cycle_ts(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")


def format_valid_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_valid_time(valid_time: str) -> datetime:
    """ "%Y-%m-%dT%H:%M:%SZ" -> aware UTC datetime. NOT interchangeable with
    parse_cycle_ts, which takes the compact "%Y%m%dT%H%M%SZ" form."""
    return datetime.strptime(valid_time, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
