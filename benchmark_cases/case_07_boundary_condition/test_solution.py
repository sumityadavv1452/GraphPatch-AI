from solution import is_valid_percentage

def test_valid_percentage():
    assert is_valid_percentage(50) is True
    assert is_valid_percentage(0) is True
    assert is_valid_percentage(100) is True
    assert is_valid_percentage(105) is False
