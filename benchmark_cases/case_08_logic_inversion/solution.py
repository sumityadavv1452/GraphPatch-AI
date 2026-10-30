def should_retry_request(status_code: int) -> bool:
    return status_code >= 500
