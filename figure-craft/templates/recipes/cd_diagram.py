"""Demšar 临界差图（FIG12）：N 个数据集上 k 个方法的平均秩，Friedman 检验后按 Nemenyi CD 连接无显著差异的方法组。

CD = q_α · sqrt(k(k+1) / (6N))，α = 0.05。秩次越小越好（分数越高者秩 1），秩 1 在左。
本实现自写；autorank（Apache-2.0）可作对照。Friedman p 值需 scipy，缺失时只报统计量。
多重比较的前提与报告格式见 research-execution 统计评价规范。
"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

Q_ALPHA_005 = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164}


def average_ranks(scores: np.ndarray) -> np.ndarray:
    """scores: 数据集 × 方法，越大越好；并列取平均秩。"""
    ranks = np.empty_like(scores, dtype=float)
    for row, values in enumerate(-scores):
        order = values.argsort()
        sorted_vals = values[order]
        r = np.empty(values.size)
        r[order] = np.arange(1, values.size + 1)
        for v in np.unique(sorted_vals):
            tie = values == v
            r[tie] = r[tie].mean()
        ranks[row] = r
    return ranks.mean(axis=0)


def friedman(scores: np.ndarray, mean_ranks: np.ndarray) -> tuple[float, float | None]:
    n, k = scores.shape
    chi2 = 12 * n / (k * (k + 1)) * (np.sum(mean_ranks ** 2) - k * (k + 1) ** 2 / 4)
    try:
        from scipy.stats import chi2 as chi2_dist
        return float(chi2), float(chi2_dist.sf(chi2, k - 1))
    except ImportError:
        return float(chi2), None


def cliques(mean_ranks: np.ndarray, cd: float) -> list[tuple[int, int]]:
    """按秩排序后，返回极大的「首尾差 < CD」区间（排序后下标）。"""
    ordered = np.sort(mean_ranks)
    spans = [(i, max(j for j in range(i, ordered.size) if ordered[j] - ordered[i] < cd))
             for i in range(ordered.size)]
    spans = [s for s in spans if s[1] > s[0]]
    return [s for s in spans if not any(o[0] <= s[0] and s[1] <= o[1] and o != s for o in spans)]


def draw(ax, names, mean_ranks, cd, args) -> None:
    k = len(names)
    order = np.argsort(mean_ranks)
    ax.set_xlim(1, k)
    ax.set_ylim(0, 1)
    ax.xaxis.set_ticks_position("top")
    ax.spines[["left", "right", "bottom"]].set_visible(False)
    ax.spines["top"].set_visible(True)
    ax.set_yticks([])
    half = (k + 1) // 2
    for pos, idx in enumerate(order):
        left = pos < half
        y = 0.75 - 0.14 * (pos if left else k - 1 - pos)
        x_end = 1 if left else k
        ax.plot([mean_ranks[idx], mean_ranks[idx], x_end], [1, y, y], color="black", linewidth=0.6,
                clip_on=False)
        ax.text(x_end, y, f" {names[idx]} ({mean_ranks[idx]:.2f}) " if left else f" ({mean_ranks[idx]:.2f}) {names[idx]} ",
                ha="right" if left else "left", va="center")
    for depth, (i, j) in enumerate(cliques(mean_ranks, cd)):
        ranks = np.sort(mean_ranks)
        ax.plot([ranks[i], ranks[j]], [0.88 - 0.05 * depth] * 2, color="black", linewidth=1.6)
    ax.plot([1, 1 + cd], [0.08, 0.08], color="black", linewidth=1.0)
    ax.text(1 + cd / 2, 0.11, f"CD = {cd:.2f}", ha="center", va="bottom")


def main() -> int:
    args = R.parse_args(__doc__)
    rng = np.random.default_rng(8)
    names = [R.text(args, f"方法{c}", f"M{c}") for c in "ABCDEF"]
    n_sets = 20
    scores = rng.normal(np.array([0.80, 0.78, 0.77, 0.74, 0.73, 0.70]), 0.04, (n_sets, len(names)))
    mean_ranks = average_ranks(scores)
    chi2, p = friedman(scores, mean_ranks)
    cd = Q_ALPHA_005[len(names)] * np.sqrt(len(names) * (len(names) + 1) / (6 * n_sets))
    print(f"  Friedman χ²={chi2:.2f}" + (f", p={p:.2g}" if p is not None else "（未装 scipy，未计 p 值）"))
    with R.context(args, aspect=0.42) as size:
        fig, ax = plt.subplots(figsize=size)
        draw(ax, names, mean_ranks, cd, args)
        return R.finish(fig, args, "cd_diagram", __file__)


if __name__ == "__main__":
    sys.exit(main())
