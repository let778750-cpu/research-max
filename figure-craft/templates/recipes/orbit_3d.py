"""三维轨道（FIG12）：(a) 三维视图用 set_box_aspect 保证三轴等比例；(b) 同一轨道的赤道面投影，定量读数以二维投影为准。

三维透视无法准确读距离与角度，正文论证优先用二维投影；示例为解析椭圆轨道，只演示画法。
"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

EARTH_RADIUS_KM = 6378.137


def orbit(a_km: float, e: float, inc_deg: float, raan_deg: float, n: int = 400) -> np.ndarray:
    nu = np.linspace(0, 2 * np.pi, n)
    r = a_km * (1 - e ** 2) / (1 + e * np.cos(nu))
    xyz = np.vstack([r * np.cos(nu), r * np.sin(nu), np.zeros_like(nu)])
    inc, raan = np.radians(inc_deg), np.radians(raan_deg)
    rot_x = np.array([[1, 0, 0], [0, np.cos(inc), -np.sin(inc)], [0, np.sin(inc), np.cos(inc)]])
    rot_z = np.array([[np.cos(raan), -np.sin(raan), 0], [np.sin(raan), np.cos(raan), 0], [0, 0, 1]])
    return rot_z @ rot_x @ xyz / 1000.0


def main() -> int:
    args = R.parse_args(__doc__, default_width="double")
    orbits = {R.text(args, "轨道 1", "Orbit 1"): orbit(7000, 0.01, 98, 0),
              R.text(args, "轨道 2", "Orbit 2"): orbit(12000, 0.35, 55, 60)}
    radius = EARTH_RADIUS_KM / 1000.0
    with R.context(args, aspect=0.45) as size:
        fig = plt.figure(figsize=size)
        ax3 = fig.add_subplot(1, 2, 1, projection="3d")
        ax2 = fig.add_subplot(1, 2, 2)
        u, v = np.meshgrid(np.linspace(0, 2 * np.pi, 24), np.linspace(0, np.pi, 12))
        ax3.plot_wireframe(radius * np.cos(u) * np.sin(v), radius * np.sin(u) * np.sin(v), radius * np.cos(v),
                           color="0.75", linewidth=0.3)
        for (name, xyz), style in zip(orbits.items(), ("-", "--")):
            ax3.plot(*xyz, linestyle=style, label=name)
            ax2.plot(xyz[0], xyz[1], linestyle=style, label=name)
        limit = max(np.abs(xyz).max() for xyz in orbits.values())
        for setter in (ax3.set_xlim, ax3.set_ylim, ax3.set_zlim):
            setter(-limit, limit)
        ax3.set_box_aspect((1, 1, 1))
        unit = R.text(args, " / 10³ km", " / 10³ km")
        ax3.set(xlabel="x" + unit, ylabel="y" + unit, zlabel="z" + unit)
        ax2.add_patch(plt.Circle((0, 0), radius, color="0.85", zorder=0))
        ax2.set_aspect("equal")
        ax2.set(xlabel="x" + unit, ylabel="y" + unit)
        from matplotlib.ticker import MaxNLocator
        for axis in (ax3.xaxis, ax3.yaxis, ax3.zaxis):
            axis.set_major_locator(MaxNLocator(3))
        handles, labels = ax2.get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside upper center", ncols=len(labels))
        R.figstyle.add_panel_labels([ax3, ax2], args.profile)
        return R.finish(fig, args, "orbit_3d", __file__)


if __name__ == "__main__":
    sys.exit(main())
