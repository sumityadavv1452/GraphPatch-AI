from solution import format_user_badge

def test_format_user_badge():
    assert format_user_badge("alice", 100) == "alice#100"
