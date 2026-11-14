# SPDX-License-Identifier: AGPL-3.0-only
"""Estimate marker-to-camera transforms using measured camera intrinsics."""
import cv2
import numpy as np
from .core import positive


def marker_points(length_m):
    h = positive(length_m, "marker_size_m") / 2
    # Top-left, top-right, bottom-right, bottom-left in marker coordinates.
    return np.array([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]], np.float64)


def detect_poses(image, camera, marker_size_m, dictionary="DICT_4X4_50"):
    if image is None or image.ndim not in (2, 3):
        raise ValueError("a readable image is required")
    marker_size_m = positive(marker_size_m, "marker_size_m")
    if list(camera["image_size"]) != [image.shape[1], image.shape[0]]:
        raise ValueError("image dimensions do not match calibration; recalibrate or rescale K")
    k = np.asarray(camera["camera_matrix"], dtype=np.float64)
    d = np.asarray(camera["dist_coeffs"], dtype=np.float64)
    if (k.shape != (3, 3) or not np.isfinite(k).all() or k[0, 0] <= 0
            or k[1, 1] <= 0 or not np.allclose(k[2], [0, 0, 1])):
        raise ValueError("invalid camera_matrix")
    if d.size not in (4, 5, 8, 12, 14) or not np.isfinite(d).all():
        raise ValueError("invalid dist_coeffs")
    if dictionary not in {"DICT_4X4_50", "DICT_4X4_100", "DICT_6X6_50", "DICT_6X6_250"}:
        raise ValueError("unsupported marker dictionary")
    dictionary_obj = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, dictionary))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    if hasattr(cv2.aruco, "ArucoDetector"):
        corners, ids, _ = cv2.aruco.ArucoDetector(dictionary_obj).detectMarkers(gray)
    else:
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary_obj)
    result = []
    annotated = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    if ids is None:
        return annotated, result
    cv2.aruco.drawDetectedMarkers(annotated, corners, ids)
    obj = marker_points(marker_size_m)
    for image_points, marker_id in zip(corners, ids.ravel()):
        ok, rvec, tvec = cv2.solvePnP(obj, image_points.reshape(4, 2).astype(np.float64),
                                    k, d, flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok or not np.isfinite(tvec).all() or tvec[2, 0] <= 0:
            continue
        projected, _ = cv2.projectPoints(obj, rvec, tvec, k, d)
        error = projected.reshape(4, 2) - image_points.reshape(4, 2)
        rmse = float(np.sqrt(np.mean(np.sum(error ** 2, axis=1))))
        cv2.drawFrameAxes(annotated, k, d, rvec, tvec, marker_size_m / 2)
        rotation, _ = cv2.Rodrigues(rvec)
        result.append({"id": int(marker_id), "translation_m": tvec.ravel().tolist(),
                       "rotation_vector_rad": rvec.ravel().tolist(),
                       "camera_position_in_marker_m": (-rotation.T @ tvec).ravel().tolist(),
                       "reprojection_rmse_px": rmse})
    return annotated, result
