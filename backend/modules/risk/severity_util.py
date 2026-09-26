"""
Risk Severity Utility (PERSON 3 MODULE)
Public interface for calculating combined risk/interaction severity scores.
"""

from typing import List, Dict, Any


def classify_severity(interactions: List[Dict[str, Any]]) -> str:
    """
    Public Service Function for Person 3:
    Evaluates list of interaction records and returns overall severity level:
    'none', 'low', 'medium', 'high', 'critical'.
    """
    if not interactions:
        return "none"

    severities = [item.get("severity", "low").lower() for item in interactions]
    if "critical" in severities:
        return "critical"
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    if "low" in severities:
        return "low"
    return "none"
