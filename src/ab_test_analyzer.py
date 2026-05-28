"""
Statistical analysis of A/B tests across creatives.

For campaigns with 2+ creatives, compares performance using a z-test
for proportions (CTR) to determine statistical significance and
identify a winner with a confidence level.
"""

import math
import sys


def _z_test_proportions(p1, n1, p2, n2):
    """Perform a two-proportion z-test.

    Tests whether two proportions (e.g., CTR of two creatives) are
    significantly different.

    Args:
        p1: Proportion for group 1 (e.g., clicks/impressions).
        n1: Sample size for group 1 (e.g., impressions).
        p2: Proportion for group 2.
        n2: Sample size for group 2.

    Returns:
        Tuple of (z_score, p_value).
    """
    # Pooled proportion
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)

    # Avoid division by zero
    if p_pool == 0 or p_pool == 1:
        return 0.0, 1.0

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0

    z = (p1 - p2) / se

    # Approximate two-tailed p-value using the complementary error function
    p_value = math.erfc(abs(z) / math.sqrt(2))

    return z, p_value


def _confidence_from_p(p_value):
    """Convert a p-value to a confidence percentage.

    Args:
        p_value: Statistical p-value (0 to 1).

    Returns:
        Confidence percentage (0 to 100).
    """
    return round((1 - p_value) * 100, 1)


def analyze_ab_test(creatives):
    """Analyze A/B test performance across creatives.

    Compares CTR (click-through rate) between creatives using a z-test
    for proportions. For campaigns with more than 2 creatives, the top
    two by impressions are compared, and all creatives are ranked.

    Args:
        creatives: List of dicts, each with at minimum:
            'id' (str) - Creative identifier.
            'impressions' (int) - Number of impressions.
            'clicks' (int) - Number of clicks.
            Optional: 'name' (str) - Creative display name.

    Returns:
        Dict with keys:
            'winner': str - ID of the winning creative.
            'winner_name': str - Name of the winner.
            'confidence': float - Confidence level (0-100).
            'significant': bool - Whether the result is statistically
                                  significant at 95% confidence.
            'lift': str - Percentage lift of winner over runner-up
                          (e.g., '+23.4%').
            'winner_ctr': float - Winner's CTR percentage.
            'runner_up_ctr': float - Runner-up's CTR percentage.
            'rankings': list - All creatives ranked by CTR.
            'sample_sizes_adequate': bool - Whether sample sizes are
                                            large enough for reliable results.
            'error': str - Error message if analysis could not be performed.
    """
    result = {
        'winner': '',
        'winner_name': '',
        'confidence': 0.0,
        'significant': False,
        'lift': '+0%',
        'winner_ctr': 0.0,
        'runner_up_ctr': 0.0,
        'rankings': [],
        'sample_sizes_adequate': False,
        'error': '',
    }

    if not creatives or len(creatives) < 2:
        result['error'] = 'Need at least 2 creatives for A/B test analysis.'
        return result

    # Filter out creatives with zero impressions
    valid = [c for c in creatives if (c.get('impressions') or 0) > 0]
    if len(valid) < 2:
        result['error'] = 'Not enough creatives with impressions for comparison.'
        return result

    # Calculate CTR for each creative
    for c in valid:
        imp = c.get('impressions') or 0
        clk = c.get('clicks') or 0
        c['_ctr'] = (clk / imp * 100) if imp > 0 else 0

    # Rank by CTR
    ranked = sorted(valid, key=lambda c: c['_ctr'], reverse=True)
    result['rankings'] = [
        {
            'id': c.get('id', ''),
            'name': c.get('name', f"Creative {c.get('id', '?')}"),
            'impressions': c.get('impressions', 0),
            'clicks': c.get('clicks', 0),
            'ctr': round(c['_ctr'], 2),
        }
        for c in ranked
    ]

    # Compare top 2
    a = ranked[0]
    b = ranked[1]

    imp_a = a.get('impressions', 0)
    clk_a = a.get('clicks', 0)
    imp_b = b.get('impressions', 0)
    clk_b = b.get('clicks', 0)

    # Check minimum sample sizes (rule of thumb: at least 100 per group)
    min_sample = 100
    result['sample_sizes_adequate'] = (imp_a >= min_sample and imp_b >= min_sample)

    if not result['sample_sizes_adequate']:
        print("  Warning: A/B test sample sizes may be too small for "
              "reliable statistical significance.", file=sys.stderr)

    # Proportions
    p_a = clk_a / imp_a if imp_a else 0
    p_b = clk_b / imp_b if imp_b else 0

    z_score, p_value = _z_test_proportions(p_a, imp_a, p_b, imp_b)
    confidence = _confidence_from_p(p_value)

    result['winner'] = a.get('id', '')
    result['winner_name'] = a.get('name', f"Creative {a.get('id', '?')}")
    result['confidence'] = confidence
    result['significant'] = confidence >= 95.0
    result['winner_ctr'] = round(a['_ctr'], 2)
    result['runner_up_ctr'] = round(b['_ctr'], 2)

    # Calculate lift
    if b['_ctr'] > 0:
        lift = ((a['_ctr'] - b['_ctr']) / b['_ctr']) * 100
        result['lift'] = f'+{lift:.1f}%' if lift >= 0 else f'{lift:.1f}%'
    elif a['_ctr'] > 0:
        result['lift'] = '+inf%'
    else:
        result['lift'] = '+0%'

    # Clean up temp field
    for c in valid:
        c.pop('_ctr', None)

    return result


def analyze_campaign_creatives(campaign):
    """Convenience function to analyze creatives within a campaign dict.

    Args:
        campaign: A campaign dict as returned by LinkedInClient, containing
                  a 'creatives' list.

    Returns:
        A/B test result dict (same as analyze_ab_test), or None if the
        campaign has fewer than 2 creatives.
    """
    creatives = campaign.get('creatives', [])
    if len(creatives) < 2:
        return None
    return analyze_ab_test(creatives)
