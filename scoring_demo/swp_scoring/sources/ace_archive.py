"""The official ground truth (spec section 2): NOAA SWPC's monthly ACE
SWEPAM hourly files, YYYYMM_ace_swepam_1h.txt.

Each data row is

    YR MO DA HHMM  MJD  SecOfDay  S  Density  Speed  Temperature

where S is a status flag documented in the file header as "0 = nominal
data, 1 to 8 = bad data record, 9 = no data", and missing values are
-9999.9. Validity (which statuses count, the sentinel) comes from
config/competition.toml, not from here.

Timestamps are taken as UTC from the YR MO DA HHMM columns, and v(t) is
the row stamped t. Within one file a duplicated timestamp keeps the last
row.
"""

import logging
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from ..core.types import CompetitionContract, format_valid_time
from .base import load_sources_config

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ArchiveRow:
    valid_time: str  # core.types.format_valid_time form
    status: int
    speed: float

    def is_valid(self, contract: CompetitionContract) -> bool:
        return (
            self.status in contract.accepted_status
            and self.speed != contract.missing_sentinel
        )


def parse(text: str) -> list[ArchiveRow]:
    rows: dict[str, ArchiveRow] = {}
    for line in text.splitlines():
        if not line.strip() or line[0] in "#:":
            continue
        parts = line.split()
        if len(parts) < 10:
            continue
        try:
            stamp = datetime(
                int(parts[0]),
                int(parts[1]),
                int(parts[2]),
                int(parts[3][:2]),
                int(parts[3][2:]),
                tzinfo=timezone.utc,
            )
            row = ArchiveRow(
                format_valid_time(stamp), int(parts[6]), float(parts[8])
            )
        except ValueError:
            log.warning("skipping unparseable archive line: %r", line)
            continue
        if row.valid_time in rows:
            log.warning(
                "duplicate archive timestamp %s, keeping the last row",
                row.valid_time,
            )
        rows[row.valid_time] = row
    return list(rows.values())


def month_url(yyyymm: str, config: dict | None = None) -> str:
    config = config or load_sources_config()["ace_archive"]
    return f"{config['base_url']}/{config['filename_template'].format(yyyymm=yyyymm)}"


def fetch_text(url: str) -> str:
    """stdlib urllib, not requests: the Lambda Python runtime ships boto3
    but not requests, and this runs inside collect_observations."""
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("ascii", errors="replace")


def fetch_month(yyyymm: str, config: dict | None = None) -> list[ArchiveRow]:
    return parse(fetch_text(month_url(yyyymm, config)))


def months_between(start: datetime, end: datetime) -> list[str]:
    """Every YYYYMM from start's month to end's month, inclusive."""
    months = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append(f"{year:04d}{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months
