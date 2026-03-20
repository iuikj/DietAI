from decimal import Decimal

def decimal_to_float(d: dict) -> dict:
    return {
        k: float(v) if isinstance(v, Decimal) else v
        for k, v in d.items()
    }