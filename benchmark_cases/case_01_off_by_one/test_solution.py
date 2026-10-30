from solution import get_last_n_items

def test_get_last_n():
    items = [1, 2, 3, 4, 5]
    assert get_last_n_items(items, 3) == [3, 4, 5]
    assert get_last_n_items(items, 1) == [5]
