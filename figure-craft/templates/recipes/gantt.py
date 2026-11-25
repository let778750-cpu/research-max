"""调度甘特图（FIG12）：每行一个资源；斜线框为可用窗口，实心块为已排任务，交叉线为同资源冲突段；时间轴统一 UTC 并注明历元。"""

import sys
from datetime import datetime, timedelta, timezone

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import _recipe as R

EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)
ROW_HEIGHT = 0.6


def span(start_min: float, length_min: float) -> tuple[float, float]:
    start = mdates.date2num(EPOCH + timedelta(minutes=start_min))
    return start, mdates.date2num(EPOCH + timedelta(minutes=start_min + length_min)) - start


def conflicts(tasks: list[tuple[float, float]]) -> list[tuple[float, float]]:
    ordered = sorted(tasks)
    found = []
    for (s1, l1), (s2, l2) in zip(ordered, ordered[1:]):
        if s2 < s1 + l1:
            found.append((s2, min(s1 + l1, s2 + l2) - s2))
    return found


def main() -> int:
    args = R.parse_args(__doc__, default_width="double")
    windows = {0: [(10, 40), (120, 35)], 1: [(30, 50), (150, 30)], 2: [(0, 25), (70, 60)], 3: [(95, 45)]}
    tasks = {0: [(15, 12), (125, 20)], 1: [(35, 18), (45, 15)], 2: [(80, 25)], 3: [(100, 30)]}
    task_color, conflict_color = R.figstyle.OKABE_ITO[0], R.figstyle.OKABE_ITO[1]
    with R.context(args, aspect=0.32) as size:
        fig, ax = plt.subplots(figsize=size)
        for row in windows:
            y = (row - ROW_HEIGHT / 2, ROW_HEIGHT)
            ax.broken_barh([span(*w) for w in windows[row]], y, facecolors="none", edgecolors="0.45",
                           hatch="////", linewidth=0.5)
            ax.broken_barh([span(*t) for t in tasks[row]], (row - 0.2, 0.4), facecolors=task_color)
            bad = conflicts(tasks[row])
            if bad:
                ax.broken_barh([span(*c) for c in bad], (row - 0.2, 0.4), facecolors=conflict_color,
                               edgecolors="black", hatch="xxxx", linewidth=0.5)
        ax.set_yticks(range(len(windows)), [R.text(args, f"资源 R{r + 1}", f"Resource R{r + 1}") for r in windows])
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=timezone.utc))
        ax.set_xlabel(R.text(args, "时间（UTC，历元 2026-01-01T00:00Z）", "Time (UTC, epoch 2026-01-01T00:00Z)"))
        handles = [Patch(facecolor="none", edgecolor="0.45", hatch="////", label=R.text(args, "可用窗口", "Available window")),
                   Patch(facecolor=task_color, label=R.text(args, "已排任务", "Scheduled task")),
                   Patch(facecolor=conflict_color, edgecolor="black", hatch="xxxx", label=R.text(args, "冲突", "Conflict"))]
        fig.legend(handles=handles, loc="outside upper center", ncols=3)
        return R.finish(fig, args, "gantt", __file__)


if __name__ == "__main__":
    sys.exit(main())
