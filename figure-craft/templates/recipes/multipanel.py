"""多面板（FIG7）：共享坐标与统一图例放在画布顶部，面板标号按期刊预设；同一方法在各面板同色同标记。"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

METHODS = ("A", "B", "C")
MARKERS = ("o", "s", "^")
LINESTYLES = ("-", "--", ":")


def main() -> int:
    args = R.parse_args(__doc__, default_width="double")
    rng = np.random.default_rng(4)
    sizes = np.array([10, 20, 50, 100, 200])
    with R.context(args, aspect=0.6) as size:
        fig, axes = plt.subplots(2, 2, figsize=size, sharex=True)
        for row, axis_row in enumerate(axes):
            for col, ax in enumerate(axis_row):
                for k, (name, marker, style) in enumerate(zip(METHODS, MARKERS, LINESTYLES)):
                    values = (1 + k * 0.3 + row) * np.log(sizes) * (1 + 0.2 * col) + rng.normal(0, 0.2, sizes.size)
                    ax.plot(sizes, values, marker=marker, linestyle=style, markersize=3,
                            label=R.text(args, f"方法 {name}", f"Method {name}"))
                ax.set_xscale("log")
        for ax in axes[1]:
            ax.set_xlabel(R.text(args, "规模 n", "Size n"))
        axes[0, 0].set_ylabel(R.text(args, "耗时 / s", "Time / s"))
        axes[1, 0].set_ylabel(R.text(args, "内存 / MB", "Memory / MB"))
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside upper center", ncols=len(METHODS))
        R.figstyle.add_panel_labels(axes.ravel(), args.profile)
        return R.finish(fig, args, "multipanel", __file__)


if __name__ == "__main__":
    sys.exit(main())
