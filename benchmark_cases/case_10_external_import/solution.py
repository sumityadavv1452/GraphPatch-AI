from collections.abc import Mapping

def is_mapping_type(obj) -> bool:
    return isinstance(obj, Mapping)
