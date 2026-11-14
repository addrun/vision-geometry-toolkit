import math
import pytest
from vision_geometry.core import calibrate_focal, estimate_distance


def test_calibration_and_distance_use_consistent_units():
    f = calibrate_focal(120, .2, 1)
    assert f == pytest.approx(600)
    assert estimate_distance(f, .2, 60) == pytest.approx(2)


@pytest.mark.parametrize("bad", [0, -1, math.inf, math.nan])
def test_invalid_measurements_are_rejected(bad):
    with pytest.raises(ValueError):
        estimate_distance(600, .2, bad)
    with pytest.raises(ValueError):
        calibrate_focal(120, bad, 1)
