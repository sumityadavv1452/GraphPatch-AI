from solution import should_retry_request

def test_should_retry():
    assert should_retry_request(503) is True
    assert should_retry_request(500) is True
    assert should_retry_request(200) is False
