import pytest
from clubhead_composition import WeightPort, ClubHeadComposition, calculate_head_cg


def test_symmetric_ports_cancel_to_center_cg():
    composition = ClubHeadComposition(weight_ports=[
        WeightPort(name="Heel port", mass=30.0, toe_heel=-1.0, face_back=0.0),
        WeightPort(name="Toe port", mass=30.0, toe_heel=1.0, face_back=0.0),
    ])

    toe_heel_cg, face_back_cg = calculate_head_cg(composition)

    assert toe_heel_cg == 0.0
    assert face_back_cg == 0.0


def test_calculate_head_cg_for_asymmetric_weight_ports():
    composition = ClubHeadComposition(weight_ports=[
        WeightPort(name="Heel port", mass=40.0, toe_heel=-1.2, face_back=0.3),
        WeightPort(name="Toe port", mass=20.0, toe_heel=0.9, face_back=-0.2),
        WeightPort(name="Back port", mass=15.0, toe_heel=0.1, face_back=1.4),
    ])

    toe_heel_cg, face_back_cg = calculate_head_cg(composition)

    assert toe_heel_cg == -0.38
    assert face_back_cg == pytest.approx(0.386667, abs=0.0001)


def test_weight_port_with_zero_mass_raises_value_error():
    with pytest.raises(ValueError):
        WeightPort(name="Invalid port", mass=0.0, toe_heel=0.0, face_back=0.0)


def test_weight_port_with_negative_mass_raises_value_error():
    with pytest.raises(ValueError):
        WeightPort(name="Invalid port", mass=-5.0, toe_heel=0.0, face_back=0.0)


def test_club_head_composition_with_no_ports_raises_value_error():
    with pytest.raises(ValueError):
        ClubHeadComposition(weight_ports=[])
