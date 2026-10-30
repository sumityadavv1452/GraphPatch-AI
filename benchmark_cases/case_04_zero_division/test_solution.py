from solution import calculate_ratio

def test_calculate_ratio():
    assert calculate_ratio(10, 20) == 0.5
    assert calculate_ratio(0, 0) == 0.0
