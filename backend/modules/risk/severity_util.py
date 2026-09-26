"""
Severity classification helper.
Keeps CRITICAL vs WARNING logic in one place so it's consistent
across interaction checks and anti-stacking decisions.
"""

from .schemas import SeverityLevel

# Badge styling hints for the frontend (Person 4 can use these directly)
SEVERITY_STYLE = {
    SeverityLevel.CRITICAL: {"color": "#D92D20", "label": "CRITICAL", "icon": "⚠️"},
    SeverityLevel.WARNING: {"color": "#F79009", "label": "WARNING", "icon": "⚠"},
    SeverityLevel.INFO: {"color": "#2E90FA", "label": "INFO", "icon": "ℹ️"},
}


def get_style(severity: SeverityLevel) -> dict:
    """Returns frontend display info (color/label/icon) for a severity level."""
    return SEVERITY_STYLE.get(severity, SEVERITY_STYLE[SeverityLevel.INFO])


def highest_severity(severities: list) -> SeverityLevel:
    """Given a list of SeverityLevel values, returns the most severe one."""
    if SeverityLevel.CRITICAL in severities:
        return SeverityLevel.CRITICAL
    if SeverityLevel.WARNING in severities:
        return SeverityLevel.WARNING
    return SeverityLevel.INFO


def classify_severity(interactions: list) -> str:
    """Classify interaction records for the caregiver assistant."""
    severities = [
        str(item.get("severity", "")).lower()
        for item in interactions
        if isinstance(item, dict)
    ]
    if "critical" in severities or "high" in severities:
        return "critical"
    if "warning" in severities or "medium" in severities:
        return "medium"
    return "none"
