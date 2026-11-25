"""地面轨迹（FIG12）：经度跨 ±180° 处插 NaN 断线，避免横穿全图的伪连线；等距圆柱投影，经纬度刻度带方向。

示例轨迹为圆轨道 + 地球自转的解析近似（倾角 97.5°、周期 95 min），只演示画法，不作轨道计算依据。
装有 cartopy 时可改用其坐标轴加海岸线；未装则只提示，不联网安装。
"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import _recipe as R

INCLINATION_DEG = 97.5
PERIOD_MIN = 95.0
EARTH_RATE_DEG_PER_MIN = 360.0 / 1436.07


def ground_track(minutes: np.ndarray, raan_deg: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    u = 2 * np.pi * minutes / PERIOD_MIN
    inc = np.radians(INCLINATION_DEG)
    lat = np.degrees(np.arcsin(np.sin(inc) * np.sin(u)))
    lon = np.degrees(np.arctan2(np.cos(inc) * np.sin(u), np.cos(u))) + raan_deg - EARTH_RATE_DEG_PER_MIN * minutes
    return (lon + 180) % 360 - 180, lat


def split_antimeridian(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    jumps = np.where(np.abs(np.diff(lon)) > 180)[0] + 1
    return np.insert(lon, jumps, np.nan), np.insert(lat, jumps, np.nan)


def degree_label(value: float, positive: str, negative: str) -> str:
    if value == 0:
        return "0°"
    return f"{abs(value):g}°{positive if value > 0 else negative}"


def main() -> int:
    args = R.parse_args(__doc__, default_width="double")
    minutes = np.arange(0, 3 * PERIOD_MIN, 0.5)
    lon, lat = split_antimeridian(*ground_track(minutes))
    stations = {"G1": (116.3, 39.9), "G2": (-70.7, -33.4), "G3": (18.4, 69.6)}
    with R.context(args, aspect=0.5) as size:
        fig, ax = plt.subplots(figsize=size)
        ax.plot(lon, lat, label=R.text(args, "星下点轨迹（3 圈）", "Ground track (3 revs)"))
        for name, (slon, slat) in stations.items():
            ax.plot(slon, slat, marker="^", color="black", markersize=4, linestyle="none")
            ax.annotate(name, (slon, slat), xytext=(3, 3), textcoords="offset points")
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_aspect("equal")
        ax.set_xticks(range(-180, 181, 60), [degree_label(v, "E", "W") for v in range(-180, 181, 60)])
        ax.set_yticks(range(-90, 91, 30), [degree_label(v, "N", "S") for v in range(-90, 91, 30)])
        ax.grid(True, color="0.85", linewidth=0.4)
        ax.legend(loc="lower left")
        try:
            import cartopy  # noqa: F401
            print("  已检测到 cartopy：正式出图可改用 cartopy.crs.PlateCarree 坐标轴并加 coastlines()")
        except ImportError:
            print("  未装 cartopy：本示例不画海岸线")
        return R.finish(fig, args, "ground_track", __file__)


if __name__ == "__main__":
    sys.exit(main())
