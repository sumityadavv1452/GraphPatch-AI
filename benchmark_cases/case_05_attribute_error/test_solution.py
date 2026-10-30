from solution import clean_identifier

def test_clean_identifier():
    assert clean_identifier("  AdminUser  ") == "adminuser"
