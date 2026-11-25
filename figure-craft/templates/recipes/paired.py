"""配对比较（FIG5）：(a) 同一单位前后连线；(b) 差值分布与差值均值的 95% bootstrap 区间，零线为无差异。"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R


def main() -> int:
    args = R.parse_args(__doc__)
    rng = np.random.default_rng(1)
    before = rng.normal(50, 8, 16)
    after = before + rng.normal(3, 4, 16)
    diff = after - before
    draws = rng.choice(diff, size=(4000, diff.size)).mean(axis=1)
    lo, hi = np.quantile(draws, [0.025, 0.975])
    with R.context(args, aspect=0.5) as size:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=size, width_ratios=[1.4, 1])
        for b, a in zip(before, after):
            ax1.plot([0, 1], [b, a], color="0.6", linewidth=0.6, zorder=1)
        ax1.scatter(np.zeros_like(before), before, s=10, marker="o", zorder=2)
        ax1.scatter(np.ones_like(after), after, s=10, marker="s", zorder=2)
        ax1.set_xticks([0, 1], [R.text(args, "基线", "Baseline"), R.text(args, "改进", "Improved")])
        ax1.set_xlim(-0.3, 1.3)
        ax1.set_ylabel(R.text(args, "得分", "Score"))
        ax2.scatter(rng.uniform(-0.1, 0.1, diff.size), diff, s=10, color="0.35", linewidths=0)
        ax2.errorbar(0.3, diff.mean(), yerr=[[diff.mean() - lo], [hi - diff.mean()]], fmt="o",
                     color="black", markersize=3.5, capsize=2.5)
        ax2.axhline(0, color="black", linewidth=0.6, linestyle="--")
        ax2.set_xticks([])
        ax2.set_xlim(-0.4, 0.6)
        ax2.set_ylabel(R.text(args, "差值（改进 − 基线）", "Difference (improved − baseline)"))
        R.figstyle.add_panel_labels([ax1, ax2], args.profile)
        return R.finish(fig, args, "paired", __file__)


if __name__ == "__main__":
    sys.exit(main())
