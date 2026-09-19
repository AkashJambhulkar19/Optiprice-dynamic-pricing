"""
=============================================================================
OPTIPRICE: UTILITY AND VISUALIZATION HELPERS
Formatting functions, CSS styling themes, and metrics helpers for Streamlit.
=============================================================================
"""

def format_currency(value):
    """Formats numeric value into clean currency string."""
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"${value/1_000:.1f}k"
    else:
        return f"${value:,.2f}"

def format_pct(value, sign=True):
    """Formats numeric value as percentage."""
    if sign and value > 0:
        return f"+{value:.1f}%"
    return f"{value:.1f}%"

def get_elasticity_badge(elasticity_class):
    """Returns formatted badge HTML for elasticity classification."""
    if "Inelastic" in elasticity_class:
        return '<span style="background-color:#064E3B;color:#34D399;padding:3px 8px;border-radius:4px;font-size:12px;font-weight:600;"> Inelastic (Pricing Power)</span>'
    elif "Highly Elastic" in elasticity_class:
        return '<span style="background-color:#7F1D1D;color:#F87171;padding:3px 8px;border-radius:4px;font-size:12px;font-weight:600;"> Elastic (Price Sensitive)</span>'
    else:
        return '<span style="background-color:#1E3A8A;color:#60A5FA;padding:3px 8px;border-radius:4px;font-size:12px;font-weight:600;"> Moderate Elasticity</span>'
