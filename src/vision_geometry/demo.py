# SPDX-License-Identifier: AGPL-3.0-only
"""Deterministic synthetic examples, with explicitly labelled synthetic ground truth."""
import csv
import json
from pathlib import Path
import cv2
import numpy as np
from .aruco import detect_poses
from .core import calibrate_focal, estimate_distance


def make_marker_image():
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    if hasattr(cv2.aruco, "generateImageMarker"):
        marker = cv2.aruco.generateImageMarker(dictionary, 7, 160)
    else:
        marker = cv2.aruco.drawMarker(dictionary, 7, 160)
    image = np.full((480, 640), 255, np.uint8)
    image[160:320, 240:400] = marker
    return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)


def run_demo(output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    f = calibrate_focal(120, .2, 1.)
    rows = []
    for distance, observed_height in [(0.5, 239), (1., 121), (1.5, 79), (2., 61)]:
        estimate = estimate_distance(f, .2, observed_height)
        rows.append({"synthetic_distance_m": distance, "pixel_height": observed_height,
                     "estimated_distance_m": round(estimate, 6),
                     "absolute_error_m": round(abs(estimate - distance), 6)})
    with (out / "ranging.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    camera = {"image_size": [640, 480],
              "camera_matrix": [[600, 0, 320], [0, 600, 240], [0, 0, 1]],
              "dist_coeffs": [0, 0, 0, 0, 0]}
    source = make_marker_image()
    annotated, poses = detect_poses(source, camera, .12)
    if len(poses) != 1 or poses[0]["id"] != 7:
        raise RuntimeError("synthetic marker was not recovered")
    cv2.imwrite(str(out / "aruco_input.png"), source)
    cv2.imwrite(str(out / "aruco_pose.png"), annotated)
    report = {"data_source": "synthetic, not camera measurements", "focal_px": f,
              "mean_absolute_error_m": sum(x["absolute_error_m"] for x in rows) / len(rows),
              "marker_size_m": .12, "poses": poses}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
