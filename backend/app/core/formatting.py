from __future__ import annotations


def format_inr(value: float | None) -> str | None:
    """Format a rupee amount using Indian conventions (Crore / Lakh)."""
    if value is None:
        return None
    if value >= 1e7:
        return f"Rs. {value / 1e7:.2f} Cr"
    if value >= 1e5:
        return f"Rs. {value / 1e5:.2f} L"
    return f"Rs. {value:,.2f}"
