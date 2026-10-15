#!/usr/bin/env python3
"""Plots the per-lead-time curves in a score.py report: S, RMSE, TRMSE and
bias against lead time for every model, plus the number of valid pairs.

    python3 plot_report.py                          # report.json -> curves.png
    python3 plot_report.py my-report.json -o my-curves.png

Needs matplotlib (pip install matplotlib); score.py itself doesn't.
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# Categorical slots, in a fixed order (never cycled).
SLOTS = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#6250d6",  # violet
    "#e34948",  # red
]
# The demo's models keep the same colours whatever else is in the report.
FIXED = {"persistence": 0, "recurrence_27d": 1, "climatology": 2}

PANELS = [
    ("s_curve", "Sτ (km/s) — the ranked score"),
    ("rmse_curve", "RMSEτ (km/s)"),
    ("trmse_curve", "TRMSEτ (km/s) — tail-weighted"),
    ("bias_curve", "Biasτ (km/s), predicted − observed"),
    ("n_curve", "Valid pairs Nτ (the same for every model)"),
]


def styles(names: list[str]) -> dict[str, dict]:
    """Colour follows the model. "official:<x>" (the scorer's own copy of
    baseline <x>) gets <x>'s colour, dashed."""

    def base(name):
        return name.removeprefix("official:")

    bases = list(dict.fromkeys(base(n) for n in names))
    free = [i for i in range(len(SLOTS)) if i not in FIXED.values()]
    slot = {}
    for b in bases:
        if b in FIXED:
            slot[b] = FIXED[b]
        elif free:
            slot[b] = free.pop(0)
        else:
            sys.exit(
                f"more than {len(SLOTS)} models: plot fewer at a time, "
                "so every colour stays distinguishable"
            )
    return {
        n: {
            "color": SLOTS[slot[base(n)]],
            "linestyle": "--" if base(n) != n else "-",
        }
        for n in names
    }


def style_axis(ax, title: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=10, color=INK, pad=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=8, length=0, pad=4)
    ax.set_xticks(range(0, 73, 12))
    ax.set_xlim(1, 72)


def plot(report: dict, out: Path) -> None:
    scores = report["scores"]
    names = sorted(scores, key=lambda n: scores[n]["s_final"])
    style = styles(names)
    leads = list(range(1, report["meta"]["horizon_hours"] + 1))

    fig, axes = plt.subplots(2, 3, figsize=(13, 7.2), facecolor=SURFACE)
    flat = axes.ravel()
    km_s = flat[:3]
    for ax, (field, title) in zip(flat, PANELS):
        style_axis(ax, title)
        if field == "n_curve":
            # Depends on the observations only: one line, in ink.
            ax.plot(leads, scores[names[0]][field], color=INK_SECONDARY, lw=1.6)
            ax.set_ylim(0, None)
            continue
        if field == "bias_curve":
            ax.axhline(0, color=AXIS, linewidth=1)
        for name in names:
            ax.plot(leads, scores[name][field], lw=1.6, **style[name])
    # The three km/s error curves share one scale, so they compare directly.
    lo = min(min(v for v in ax.get_ylim()) for ax in km_s)
    hi = max(max(v for v in ax.get_ylim()) for ax in km_s)
    for ax in km_s:
        ax.set_ylim(lo, hi)
    for ax in axes[1]:
        ax.set_xlabel("Lead time τ (hours)", fontsize=9, color=MUTED)

    legend_ax = flat[5]
    legend_ax.axis("off")
    for name in names:
        legend_ax.plot([], [], lw=2, label=name, **style[name])
    legend_ax.legend(
        loc="center left",
        frameon=False,
        fontsize=10,
        labelcolor=INK,
        title="Model (best S_final first)",
        title_fontsize=9,
        alignment="left",
        handlelength=2.6,
    )
    meta = report["meta"]
    fig.suptitle(
        f"Per-lead-time scores, {meta['n_cycles']} cycles, "
        f"{meta['start'][:10]} to {meta['end'][:10]}",
        x=0.01,
        ha="left",
        fontsize=12,
        color=INK,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out, dpi=130, facecolor=SURFACE)
    print(f"wrote {out}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("report", nargs="?", type=Path, default=Path("report.json"))
    ap.add_argument("-o", "--output", type=Path, default=Path("curves.png"))
    args = ap.parse_args()
    plot(json.loads(args.report.read_text()), args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
