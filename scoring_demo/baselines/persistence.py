#!/usr/bin/env python3
"""Persistence baseline: tomorrow looks like now. Every lead time gets the
most recent valid observation at or before t0.

    python3 persistence.py 20260701T000000Z   ->  forecast JSON on stdout
"""

import sys

from ace import HORIZON_HOURS, latest_at_or_before, main


def predict(t0, obs):
    return [latest_at_or_before(obs, t0)] * HORIZON_HOURS


if __name__ == "__main__":
    sys.exit(main(predict))
