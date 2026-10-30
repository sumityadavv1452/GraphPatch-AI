def normalize_color(color_name: str) -> str:
    mapping = {"red": "#FF0000", "green": "#00FF00", "blue": "#0000FF"}
    return mapping[color_name.lower()]
