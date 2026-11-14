# SPDX-License-Identifier: AGPL-3.0-only
"""Size-prior ranging. This is not a learned monocular depth estimator."""
import json
import math
from pathlib import Path


def positive(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def calibrate_focal(pixel_height, real_height_m, distance_m):
    """f [px] = image height [px] * known distance [m] / real height [m]."""
    return (positive(pixel_height, "pixel_height") * positive(distance_m, "distance_m")
            / positive(real_height_m, "real_height_m"))


def estimate_distance(focal_px, real_height_m, pixel_height):
    return (positive(focal_px, "focal_px") * positive(real_height_m, "real_height_m")
            / positive(pixel_height, "pixel_height"))


def read_ranging_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    focal = positive(config["focal_px"], "focal_px")
    heights = {str(k): positive(v, f"height[{k}]")
               for k, v in config["object_heights_m"].items()}
    if not heights:
        raise ValueError("object_heights_m must not be empty")
    return focal, heights
