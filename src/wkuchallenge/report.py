"""Charts for the README and for team updates."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GREY, BLUE, GREEN, RED = "#9aa0a6", "#1a73e8", "#34a853", "#d93025"


def pnl_chart(rows: list[dict], review_line: float, out: str | Path, title: str) -> Path:
    rows = sorted(rows, key=lambda r: r["pnl_pct"], reverse=True)
    names = [r["ticker"] for r in rows]
    vals = [r["pnl_pct"] * 100 for r in rows]
    colors = [GREEN if v >= 0 else (RED if v <= -review_line * 100 else "#f28b82") for v in vals]

    fig, ax = plt.subplots(figsize=(8, 0.45 * len(rows) + 1.4))
    ax.barh(names, vals, color=colors)
    ax.invert_yaxis()
    ax.axvline(0, color="#5f6368", lw=0.8)
    ax.axvline(-review_line * 100, color=GREY, ls="--", lw=1)
    ax.text(-review_line * 100, len(rows) - 0.4, f" review line -{review_line:.0%}", color="#5f6368", fontsize=9)
    for i, v in enumerate(vals):
        ax.text(v + (0.3 if v >= 0 else -0.3), i, f"{v:+.1f}%", va="center", ha="left" if v >= 0 else "right", fontsize=9)
    ax.set_xlabel("Gain / loss vs average cost (%)")
    ax.set_title(title, loc="left", fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    lo = min(vals + [-review_line * 100]) - 3
    ax.set_xlim(lo, max(vals + [0]) + 3)
    fig.tight_layout()
    out = Path(out)
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def allocation_chart(rows: list[dict], cash: float, out: str | Path, title: str) -> Path:
    rows = sorted(rows, key=lambda r: r["value"], reverse=True)
    labels = [r["ticker"] for r in rows] + ["Cash"]
    values = [r["value"] for r in rows] + [cash]
    total = sum(values)

    fig, ax = plt.subplots(figsize=(8, 1.9))
    left = 0.0
    for lab, v in zip(labels, values):
        w = v / total
        ax.barh(0, w, left=left, color=GREY if lab == "Cash" else BLUE, alpha=0.35 if lab == "Cash" else 0.55 + 0.4 * w,
                edgecolor="white")
        if w > 0.025:
            ax.text(left + w / 2, 0, f"{lab}\n{w:.0%}", ha="center", va="center", fontsize=8 if w > 0.045 else 6.5)
        left += w
    ax.set_xlim(0, 1)
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=12)
    fig.tight_layout()
    out = Path(out)
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out
