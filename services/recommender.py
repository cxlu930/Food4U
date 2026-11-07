# TODO: simple scoring (cuisine match + ingredients in pantry + price within budget).

from data.ingredients import CUISINES


def normalize_cuisine(value):
    """Return the CUISINES value for `value`, or None if it is not a known cuisine.

    Lowercases the input, trims it and replaces spaces with underscores,
    so "Chinese" -> "chinese" and " Western " -> "western".
    """
    if not isinstance(value, str):
        return None
    name = "_".join(value.strip().lower().split())
    return name if name in CUISINES else None
