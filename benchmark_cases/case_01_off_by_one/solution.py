def get_last_n_items(lst: list, n: int) -> list:
    if n <= 0:
        return []
    return lst[-n:]
