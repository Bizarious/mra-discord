def is_integer(obj):
    try:
        int(obj)
    except ValueError:
        raise ValueError(f"'{obj}' is no valid integer.")
