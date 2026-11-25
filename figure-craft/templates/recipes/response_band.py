"""响应曲线与分级区间带（FIG4、FIG5）：中位数线 + 50% / 80% / 95% 嵌套区间（Wilke 分级带），区间定义写进图例与图注。"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

LEVELS = (0.95, 0.80, 0.50)
ALPHAS = (0.18, 0.30, 0.45)


def main() -> int:
    args = R.parse_args(__doc__)
    rng = np.random.default_rng(2)
    x = np.linspace(0, 10, 60)
    runs = 1 - np.exp(-x[None, :] / rng.uniform(2.0, 3.5, (40, 1))) + rng.normal(0, 0.03, (40, x.size))
    with R.context(args) as size:
        fig, ax = plt.subplots(figsize=size)
        color = R.figstyle.OKABE_ITO[0]
        for level, alpha in zip(LEVELS, ALPHAS):
            lo, hi = np.quantile(runs, [(1 - level) / 2, (1 + level) / 2], axis=0)
            ax.fill_between(x, lo, hi, color=color, alpha=alpha, linewidth=0,
                            label=R.text(args, f"{level:.0%} 区间", f"{level:.0%} interval"))
        ax.plot(x, np.median(runs, axis=0), color="black", label=R.text(args, "中位数", "Median"))
        ax.set_xlabel(R.text(args, "输入 x / 单位", "Input x / unit"))
        ax.set_ylabel(R.text(args, "响应 y", "Response y"))
        ax.set_ylim(-0.1, 1.15)
        ax.legend(loc="lower right")
        return R.finish(fig, args, "response_band", __file__)


if __name__ == "__main__":
    sys.exit(main())
