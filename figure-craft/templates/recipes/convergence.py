"""收敛曲线（FIG12）：多次独立运行的中位数 + 中位数的 95% bootstrap 区间；对数纵轴，线型与标记冗余编码，不画单次最好运行。"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

RUNS = 30
BOOTSTRAP = 1000
STYLES = (("-", "o"), ("--", "s"), (":", "^"))


def median_band(curves: np.ndarray, rng: np.random.Generator):
    picks = rng.integers(0, curves.shape[0], (BOOTSTRAP, curves.shape[0]))
    medians = np.median(curves[picks], axis=1)
    return np.median(curves, axis=0), np.quantile(medians, 0.025, axis=0), np.quantile(medians, 0.975, axis=0)


def main() -> int:
    args = R.parse_args(__doc__)
    rng = np.random.default_rng(5)
    evals = np.arange(1, 201) * 50
    with R.context(args) as size:
        fig, ax = plt.subplots(figsize=size)
        for k, ((style, marker), rate) in enumerate(zip(STYLES, (0.012, 0.018, 0.025))):
            curves = np.exp(-rate * np.arange(1, 201)[None, :] * rng.uniform(0.7, 1.3, (RUNS, 1)))
            curves = np.minimum.accumulate(curves * rng.lognormal(0, 0.15, curves.shape), axis=1)
            mid, lo, hi = median_band(curves, rng)
            color = R.figstyle.OKABE_ITO[k]
            ax.fill_between(evals, lo, hi, color=color, alpha=0.25, linewidth=0)
            ax.plot(evals, mid, color=color, linestyle=style, marker=marker, markevery=25, markersize=3,
                    label=R.text(args, f"算法 {chr(65 + k)}", f"Algorithm {chr(65 + k)}"))
        ax.set_yscale("log")
        ax.set_xlabel(R.text(args, "函数评估次数", "Function evaluations"))
        ax.set_ylabel(R.text(args, "最优值误差（中位数，30 次）", "Best error (median of 30)"))
        ax.legend(loc="lower left")
        return R.finish(fig, args, "convergence", __file__)


if __name__ == "__main__":
    sys.exit(main())
