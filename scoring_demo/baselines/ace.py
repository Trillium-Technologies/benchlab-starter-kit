"""Shared by the three baseline models: reads the ACE SWEPAM hourly archive
(the competition's ground truth) and hands each model only what a
forecaster could have known at t0.

Standard library only, like a submission that brings its own data access:
nothing here imports the scorer.

Archive months are read from ../data/ace/ when the file is there (the
months shipped with this demo), otherwise fetched from NASA. Set
ACE_ARCHIVE_DIR to read them from somewhere else.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

HORIZON_HOURS = 72
HOUR = timedelta(hours=1)

ARCHIVE_URL = (
    "https://sohoftp.nascom.nasa.gov/sdb/goes/ace/monthly/"
    "{yyyymm}_ace_swepam_1h.txt"
)
LOCAL_DIR = Path(
    os.environ.get(
        "ACE_ARCHIVE_DIR",
        Path(__file__).resolve().parent.parent / "data" / "ace",
    )
)

# The same validity rule the scorer applies (config/competition.toml):
# status flag 0 only, and never the -9999.9 missing-value sentinel.
ACCEPTED_STATUS = {0}
MISSING_SENTINEL = -9999.9

# How far back any baseline looks: 27-day recurrence plus the 72 h
# persistence look-back.
HISTORY = timedelta(days=27, hours=72)


@lru_cache(maxsize=None)
def _month_text(yyyymm: str) -> str:
    local = LOCAL_DIR / f"{yyyymm}_ace_swepam_1h.txt"
    if local.exists():
        return local.read_text(encoding="ascii", errors="replace")
    url = ARCHIVE_URL.format(yyyymm=yyyymm)
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("ascii", errors="replace")


def _parse(text: str) -> dict[datetime, float]:
    """Valid rows only. Columns: YR MO DA HHMM MJD SecOfDay S Density
    Speed Temperature. A duplicated timestamp keeps the last row."""
    out: dict[datetime, float] = {}
    for line in text.splitlines():
        if not line.strip() or line[0] in "#:":
            continue
        parts = line.split()
        if len(parts) < 10:
            continue
        try:
            t = datetime(
                int(parts[0]),
                int(parts[1]),
                int(parts[2]),
                int(parts[3][:2]),
                int(parts[3][2:]),
                tzinfo=timezone.utc,
            )
            status, speed = int(parts[6]), float(parts[8])
        except ValueError:
            continue
        if status in ACCEPTED_STATUS and speed != MISSING_SENTINEL:
            out[t] = speed
        else:
            out.pop(t, None)
    return out


def _months(start: datetime, end: datetime) -> list[str]:
    months, (y, m) = [], (start.year, start.month)
    while (y, m) <= (end.year, end.month):
        months.append(f"{y:04d}{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return months


def observations_until(t0: datetime) -> dict[datetime, float]:
    """Every valid hourly speed stamped at or before t0, never after it.
    For a historical t0 the whole archive exists, so this cut-off is the
    only thing standing between a backtest and a peek at the answer."""
    obs: dict[datetime, float] = {}
    for yyyymm in _months(t0 - HISTORY, t0):
        obs.update(_parse(_month_text(yyyymm)))
    return {t: v for t, v in obs.items() if t <= t0}


def latest_at_or_before(
    obs: dict[datetime, float], t0: datetime, lookback_hours: int = 72
) -> float | None:
    """The most recent valid speed at or before t0, within lookback_hours."""
    for back in range(lookback_hours + 1):
        value = obs.get(t0 - back * HOUR)
        if value is not None:
            return value
    return None


def forecast(predict, t0: datetime) -> dict:
    """The forecast.json object a submission uploads for cycle t0."""
    speeds = predict(t0, observations_until(t0))
    if len(speeds) != HORIZON_HOURS:
        raise ValueError(f"produced {len(speeds)} values, need 72")
    return {
        "t0": t0.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "valid_from": (t0 + HOUR).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecast_speed_kms": [
            None if v is None else float(v) for v in speeds
        ],
    }


def main(predict) -> int:
    """The submission contract: argv[1] is t0, JSON forecast on stdout."""
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <YYYYMMDDTHHMMSSZ>", file=sys.stderr)
        return 2
    t0 = datetime.strptime(sys.argv[1], "%Y%m%dT%H%M%SZ").replace(
        tzinfo=timezone.utc
    )
    json.dump(forecast(predict, t0), sys.stdout)
    return 0
