import numpy as np
import pytest
from vision_geometry.aruco import detect_poses
from vision_geometry.demo import make_marker_image, run_demo

CAMERA = {"image_size": [640, 480], "camera_matrix": [[600, 0, 320], [0, 600, 240], [0, 0, 1]],
          "dist_coeffs": [0, 0, 0, 0, 0]}


def test_synthetic_marker_has_correct_metric_pose():
    _, poses = detect_poses(make_marker_image(), CAMERA, .12)
    assert len(poses) == 1 and poses[0]["id"] == 7
    assert poses[0]["translation_m"][2] == pytest.approx(.45, abs=.01)
    assert np.linalg.norm(poses[0]["translation_m"][:2]) < .005
    assert poses[0]["reprojection_rmse_px"] < .1


def test_no_marker_and_mismatched_calibration():
    _, poses = detect_poses(np.full((480, 640, 3), 255, np.uint8), CAMERA, .12)
    assert poses == []
    with pytest.raises(ValueError, match="dimensions"):
        detect_poses(np.zeros((240, 320, 3), np.uint8), CAMERA, .12)


def test_demo_writes_inspectable_results(tmp_path):
    report = run_demo(tmp_path)
    assert report["data_source"].startswith("synthetic")
    assert (tmp_path / "ranging.csv").is_file()
    assert (tmp_path / "aruco_pose.png").is_file()
