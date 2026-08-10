"""
Rule-based ML safety predictor for the Boat Safety System.

Inputs come from the CV service and are evaluated against
maritime safety heuristics to produce a three-level safety label.
"""


def predict_safety(
    people_count: int,
    overcrowded: bool,
    stepped_out: bool,
    life_jacket_ok: bool,
) -> str:
    """
    Returns one of: "Unsafe", "Caution", "Safe"

    Priority (highest → lowest):
        1. Overcrowded or someone stepped out of bounds → Unsafe
        2. No life jacket detected → Caution
        3. Otherwise → Safe
    """
    if overcrowded or stepped_out:
        return "Unsafe"
    if not life_jacket_ok:
        return "Caution"
    return "Safe"


def safety_color(level: str) -> str:
    """Returns a Bootstrap color class for the given safety level."""
    return {
        "Unsafe": "danger",
        "Caution": "warning",
        "Safe": "success",
    }.get(level, "secondary")
