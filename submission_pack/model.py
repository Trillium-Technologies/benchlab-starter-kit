#!/usr/bin/env python3
# Example submission. Replace with anything — this exists to show the shape
# of the contract, not to constrain your language.
#
# Usage:  python3 model.py 20261111T060000Z   ->  JSON on stdout

import json
import sys
from datetime import datetime, timedelta, timezone

FORECAST_HOURS = 72


def predict(t0):
    # Return 72 hourly solar wind speeds (km/s) for t0+1h .. t0+72h.
    # Flat persistence: a floor, not a model.
    return [420.0] * FORECAST_HOURS


def main():
    if len(sys.argv) != 2:
        print("usage: model.py <YYYYMMDDTHHMMSSZ>", file=sys.stderr)
        return 2

    t0 = datetime.strptime(sys.argv[1], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    speeds = predict(t0)

    if len(speeds) != FORECAST_HOURS:
        print(
            "FATAL: produced %d values, need %d" % (len(speeds), FORECAST_HOURS),
            file=sys.stderr,
        )
        return 3

    json.dump(
        {
            "t0": t0.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "valid_from": (t0 + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "forecast_speed_kms": [float(v) for v in speeds],
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
