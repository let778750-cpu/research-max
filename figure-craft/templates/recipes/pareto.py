"""Pareto 前沿（FIG12）：灰色参考前沿 + 各算法非支配解（标记冗余），图例附 HV 与 IGD；两目标均为最小化。

HV 以参考点 REF 计算，IGD 以参考前沿采样点计算；二者定义、参考点与归一化方式须写进图注。
"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

REF = np.array([1.1, 1.1])
MARKERS = ("o", "s", "^")


def nondominated(points: np.ndarray) -> np.ndarray:
    keep = [i for i, p in enumerate(points)
            if not np.any(np.all(points <= p, axis=1) & np.any(points < p, axis=1))]
    front = points[keep]
    return front[np.argsort(front[:, 0])]


def hypervolume_2d(front: np.ndarray, ref: np.ndarray = REF) -> float:
    inside = front[np.all(front < ref, axis=1)]
    if inside.size == 0:
        return 0.0
    inside = inside[np.argsort(inside[:, 0])]
    right = np.append(inside[1:, 0], ref[0])
    return float(np.sum((right - inside[:, 0]) * (ref[1] - inside[:, 1])))


def igd(front: np.ndarray, reference: np.ndarray) -> float:
    distances = np.linalg.norm(reference[:, None, :] - front[None, :, :], axis=2)
    return float(distances.min(axis=1).mean())


def main() -> int:
    args = R.parse_args(__doc__)
    rng = np.random.default_rng(6)
    f1 = np.linspace(0, 1, 200)
    reference = np.column_stack([f1, 1 - np.sqrt(f1)])
    with R.context(args, aspect=0.8) as size:
        fig, ax = plt.subplots(figsize=size)
        ax.plot(reference[:, 0], reference[:, 1], color="0.6", linewidth=1.6,
                label=R.text(args, "参考前沿", "Reference front"), zorder=1)
        for k, (gap, marker) in enumerate(zip((0.02, 0.06, 0.12), MARKERS)):
            x = rng.uniform(0, 1, 60)
            cloud = np.column_stack([x, 1 - np.sqrt(x) + gap + rng.exponential(gap, x.size)])
            front = nondominated(cloud)
            label = f"{chr(65 + k)} (HV={hypervolume_2d(front):.3f}, IGD={igd(front, reference):.3f})"
            ax.plot(front[:, 0], front[:, 1], marker=marker, markersize=3.5, linewidth=0.8, label=label, zorder=2)
        ax.set_xlabel(R.text(args, "目标 1 $f_1$（最小化）", "Objective $f_1$ (minimize)"))
        ax.set_ylabel(R.text(args, "目标 2 $f_2$（最小化）", "Objective $f_2$ (minimize)"))
        ax.set_xlim(-0.02, 1.05)
        ax.set_ylim(-0.02, 1.45)
        ax.legend(loc="upper right")
        return R.finish(fig, args, "pareto", __file__)


if __name__ == "__main__":
    sys.exit(main())
