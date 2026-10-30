from solution import peek_front

def test_peek_front():
    assert peek_front([1, 2]) == 1
    assert peek_front([]) is None
