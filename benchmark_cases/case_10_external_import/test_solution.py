from solution import is_mapping_type

def test_is_mapping_type():
    assert is_mapping_type({"a": 1}) is True
    assert is_mapping_type([1, 2]) is False
