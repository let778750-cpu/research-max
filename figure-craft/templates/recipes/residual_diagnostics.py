"""残差诊断四联（FIG6）：残差—拟合值、正态 Q-Q、尺度—位置、残差—观测顺序；四联定义与判读见误差与分布参考文件。"""

import sys
from statistics import NormalDist

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R


def main() -> int:
    args = R.parse_args(__doc__, default_width="double")
    rng = np.random.default_rng(3)
    x = np.sort(rng.uniform(0, 10, 120))
    y = 1.5 + 0.8 * x + rng.normal(0, 0.4 + 0.05 * x)
    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x
    resid = y - fitted
    std = resid / resid.std(ddof=2)
    order = rng.permutation(resid.size)
    theory = [NormalDist().inv_cdf((i - 0.5) / resid.size) for i in range(1, resid.size + 1)]
    with R.context(args, aspect=0.55) as size:
        fig, axes = plt.subplots(2, 2, figsize=size)
        a, b, c, d = axes.ravel()
        a.scatter(fitted, resid, s=6, linewidths=0)
        a.axhline(0, color="black", linewidth=0.6, linestyle="--")
        a.set(xlabel=R.text(args, "拟合值", "Fitted value"), ylabel=R.text(args, "残差", "Residual"))
        b.scatter(theory, np.sort(std), s=6, linewidths=0)
        b.plot([-3, 3], [-3, 3], color="black", linewidth=0.6, linestyle="--")
        b.set(xlabel=R.text(args, "理论分位数", "Theoretical quantile"),
              ylabel=R.text(args, "标准化残差分位数", "Standardized residual"))
        c.scatter(fitted, np.sqrt(np.abs(std)), s=6, linewidths=0)
        c.set(xlabel=R.text(args, "拟合值", "Fitted value"), ylabel=r"$\sqrt{|r_{\mathrm{std}}|}$")
        d.plot(np.arange(resid.size), resid[order], marker="o", markersize=2, linewidth=0.5)
        d.axhline(0, color="black", linewidth=0.6, linestyle="--")
        d.set(xlabel=R.text(args, "观测顺序", "Observation order"), ylabel=R.text(args, "残差", "Residual"))
        R.figstyle.add_panel_labels(axes.ravel(), args.profile)
        return R.finish(fig, args, "residual_diagnostics", __file__)


if __name__ == "__main__":
    sys.exit(main())
