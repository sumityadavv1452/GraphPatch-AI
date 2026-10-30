def get_config_timeout(config: dict) -> int:
    return config.get("timeout", 10)
