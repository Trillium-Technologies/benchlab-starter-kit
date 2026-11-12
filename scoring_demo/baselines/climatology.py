#!/usr/bin/env python3
"""Climatology baseline: the same constant for every cycle and lead time.

The constant is the mean ACE bulk speed over 2025-10 .. 2026-09 (the twelve
complete months before the competition), fixed in advance and never
recomputed from the evaluation period. It is [baselines] climatology_kms in
the scorer's config/competition.toml.

    python3 climatology.py 20260701T000000Z   ->  forecast JSON on stdout
"""

import sys

from ace import HORIZON_HOURS, main

CLIMATOLOGY_KMS = 469.5


def predict(t0, obs):
    return [CLIMATOLOGY_KMS] * HORIZON_HOURS


if __name__ == "__main__":
    sys.exit(main(predict))
