from solution import get_config_timeout

def test_config_timeout():
    assert get_config_timeout({"timeout": 30}) == 30
    assert get_config_timeout({}) == 10
