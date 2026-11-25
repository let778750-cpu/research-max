"""Dolan–Moré 性能剖面（FIG12）：ρ_s(τ) 为求解器 s 在比值 ≤ τ 内解出的问题比例；横轴 log2 τ，失败记为无穷大（曲线不到 1）。

代价矩阵须同一预算、同一停止判据；失败与超时的判定写进图注。
"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

STYLES = ("-", "--", ":", "-.")


def performance_profile(costs: np.ndarray, taus: np.ndarray) -> np.ndarray:
    """costs: 问题 × 求解器，失败为 np.inf；返回 求解器 × τ 的 ρ 值。"""
    best = np.min(costs, axis=1, keepdims=True)
    solvable = np.isfinite(best[:, 0])
    ratios = costs[solvable] / best[solvable]
    return np.array([[np.mean(ratios[:, s] <= tau) * solvable.mean() for tau in taus]
                     for s in range(costs.shape[1])])


def main() -> int:
    args = R.parse_args(__doc__)
    rng = np.random.default_rng(7)
    problems, solvers = 80, 4
    costs = rng.lognormal(mean=np.array([0.0, 0.2, 0.4, 0.1]), sigma=0.6, size=(problems, solvers))
    costs[rng.random((problems, solvers)) < np.array([0.02, 0.05, 0.0, 0.15])] = np.inf
    taus = 2.0 ** np.linspace(0, 5, 400)
    rho = performance_profile(costs, taus)
    with R.context(args) as size:
        fig, ax = plt.subplots(figsize=size)
        for s, style in enumerate(STYLES):
            ax.step(np.log2(taus), rho[s], where="post", linestyle=style,
                    label=R.text(args, f"求解器 {s + 1}", f"Solver {s + 1}"))
        ax.set_xlabel(r"$\log_2 \tau$")
        ax.set_ylabel(R.text(args, r"问题比例 $\rho_s(\tau)$", r"Fraction of problems $\rho_s(\tau)$"))
        ax.set_xlim(0, 5)
        ax.set_ylim(0, 1.02)
        ax.legend(loc="lower right")
        return R.finish(fig, args, "performance_profile", __file__)


if __name__ == "__main__":
    sys.exit(main())
