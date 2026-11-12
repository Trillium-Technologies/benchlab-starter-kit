#!/usr/bin/env python3
"""27-day recurrence baseline: the Sun rotates roughly every 27 days as seen
from Earth, so v_hat(t0 + tau) = v(t0 + tau - 27 days). Where that
observation is missing it falls back to persistence. Since tau <= 72 h,
every value it reads is from before t0.

    python3 recurrence_27d.py 20260701T000000Z   ->  forecast JSON on stdout
"""

import sys
from datetime import timedelta

from ace import HORIZON_HOURS, HOUR, latest_at_or_before, main

PERIOD = timedelta(days=27)


def predict(t0, obs):
    fallback = latest_at_or_before(obs, t0)
    return [
        obs.get(t0 + tau * HOUR - PERIOD, fallback)
        for tau in range(1, HORIZON_HOURS + 1)
    ]


if __name__ == "__main__":
    sys.exit(main(predict))
