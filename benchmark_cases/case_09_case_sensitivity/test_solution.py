from solution import normalize_color

def test_normalize_color():
    assert normalize_color("RED") == "#FF0000"
    assert normalize_color("green") == "#00FF00"
