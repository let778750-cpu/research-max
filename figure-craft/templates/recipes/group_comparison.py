"""组间比较（FIG3、FIG5）：逐点显示原始观测，叠加均值与 95% bootstrap 区间；不用均值柱状图掩盖分布。"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

BOOTSTRAP = 4000


def bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator, level: float = 0.95):
    draws = rng.choice(values, size=(BOOTSTRAP, values.size), replace=True).mean(axis=1)
    lo, hi = np.quantile(draws, [(1 - level) / 2, (1 + level) / 2])
    return values.mean(), lo, hi


def main() -> int:
    args = R.parse_args(__doc__)
    rng = np.random.default_rng(0)
    groups = {"A": rng.normal(10, 1.2, 18), "B": rng.normal(11.2, 1.5, 22), "C": rng.lognormal(2.45, 0.12, 15)}
    markers = ["o", "s", "^"]
    with R.context(args, aspect=0.75) as size:
        fig, ax = plt.subplots(figsize=size)
        for index, ((name, values), marker) in enumerate(zip(groups.items(), markers)):
            jitter = rng.uniform(-0.12, 0.12, values.size)
            ax.scatter(index + jitter, values, s=9, marker=marker, alpha=0.6, linewidths=0, zorder=2)
            mean, lo, hi = bootstrap_mean_ci(values, rng)
            ax.errorbar(index + 0.3, mean, yerr=[[mean - lo], [hi - mean]], fmt="o", color="black",
                        markersize=3.5, capsize=2.5, zorder=3)
        ax.set_xticks(range(len(groups)), [R.text(args, f"方法 {k}", f"Method {k}") for k in groups])
        ax.set_xlim(-0.5, len(groups) - 0.3)
        ax.set_ylabel(R.text(args, "指标 y / 单位", "Metric y / unit"))
        return R.finish(fig, args, "group_comparison", __file__)


if __name__ == "__main__":
    sys.exit(main())
