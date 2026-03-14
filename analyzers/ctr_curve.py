"""
CTR Curve Model

Industry-standard Google CTR curve.
Used to detect pages performing BELOW their expected CTR
given their position — making issue detection accurate.
"""

# Google average CTR by position (industry benchmark)
CTR_CURVE = {
    1:  0.284,
    2:  0.152,
    3:  0.108,
    4:  0.079,
    5:  0.061,
    6:  0.050,
    7:  0.040,
    8:  0.032,
    9:  0.025,
    10: 0.020,
    11: 0.014,
    12: 0.011,
    13: 0.009,
    14: 0.007,
    15: 0.006,
    16: 0.005,
    17: 0.004,
    18: 0.004,
    19: 0.003,
    20: 0.003,
}
 

def expected_ctr(position: float) -> float:
    """
    Return the industry-expected CTR for a given position.
    Uses interpolation for decimal positions.
    """
    if position <= 0:
        return CTR_CURVE[1]

    pos_int = int(position)
    pos_frac = position - pos_int

    if pos_int >= 20:
        return 0.002

    low  = CTR_CURVE.get(pos_int, 0.002)
    high = CTR_CURVE.get(pos_int + 1, 0.002)

    # Linear interpolation between positions
    return round(low + (high - low) * pos_frac, 6)


def ctr_gap(actual_ctr: float, position: float) -> float:
    """
    How much CTR is being lost vs industry average.
    Positive = underperforming. Negative = overperforming.
    """
    return round(expected_ctr(position) - actual_ctr, 6)


def ctr_performance_ratio(actual_ctr: float, position: float) -> float:
    """
    Ratio of actual vs expected CTR.
    < 0.6 = significantly underperforming (flag as Low CTR issue)
    > 1.0 = outperforming (star page)
    """
    exp = expected_ctr(position)
    if exp == 0:
        return 1.0
    return round(actual_ctr / exp, 4)


def ctr_label(ratio: float) -> str:
    """Human-readable CTR performance label"""
    if ratio >= 1.2:
        return "⭐ Above Average"
    elif ratio >= 0.8:
        return "✅ On Target"
    elif ratio >= 0.6:
        return "🟡 Below Average"
    elif ratio >= 0.4:
        return "🟠 Poor"
    else:
        return "🔴 Critical"


def opportunity_clicks(impressions: int, actual_ctr: float, position: float,
                       target_ratio: float = 0.85) -> int:
    """
    Estimate additional clicks if CTR improves to target_ratio × expected.
    Realistic: we don't assume 100% of expected is achievable.
    """
    target_ctr = expected_ctr(position) * target_ratio
    if target_ctr <= actual_ctr:
        return 0
    return max(0, int(impressions * (target_ctr - actual_ctr)))