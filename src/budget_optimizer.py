"""
Optimize budget allocation across campaigns.

Calculates an efficiency score for each campaign based on CTR, CPC,
and engagement rate, then suggests budget reallocation to maximize
overall campaign performance.
"""

import sys


# Weights for efficiency score calculation
WEIGHT_CTR = 0.40
WEIGHT_CPC_INV = 0.35  # Inverse CPC (lower CPC = better)
WEIGHT_ENGAGEMENT = 0.25


def _calculate_efficiency_score(campaign, max_ctr, max_cpc, max_eng_rate):
    """Calculate a normalized efficiency score for a campaign.

    The score combines CTR, inverse CPC, and engagement rate into a
    single 0-100 metric.

    Args:
        campaign: Campaign dict with metrics.
        max_ctr: Maximum CTR across all campaigns (for normalization).
        max_cpc: Maximum CPC across all campaigns (for normalization).
        max_eng_rate: Maximum engagement rate across all campaigns.

    Returns:
        Float score from 0 to 100.
    """
    ctr = campaign.get('ctr') or 0
    cpc = campaign.get('cpc') or 0
    eng_rate = campaign.get('engagement_rate') or 0

    # Normalize each metric to 0-1 range
    norm_ctr = (ctr / max_ctr) if max_ctr > 0 else 0
    # Inverse CPC: lower is better, so we invert
    norm_cpc_inv = (1 - (cpc / max_cpc)) if max_cpc > 0 and cpc > 0 else 0
    norm_eng = (eng_rate / max_eng_rate) if max_eng_rate > 0 else 0

    score = (
        WEIGHT_CTR * norm_ctr
        + WEIGHT_CPC_INV * norm_cpc_inv
        + WEIGHT_ENGAGEMENT * norm_eng
    ) * 100

    return round(score, 1)


def optimize_budget(campaigns, total_budget=None):
    """Suggest budget reallocation across campaigns based on efficiency.

    Calculates an efficiency score per campaign using a weighted
    combination of CTR, inverse CPC, and engagement rate. Allocates
    more budget to efficient campaigns and less to poor performers.

    Args:
        campaigns: List of campaign dicts, each containing at minimum:
            'id', 'display_name' or 'name', 'impressions', 'clicks',
            'cost_usd', 'ctr', 'cpc', 'engagement_rate'.
        total_budget: Total budget to allocate. If None, uses the sum
                      of current campaign spend.

    Returns:
        List of dicts, one per campaign, each with keys:
            'id': str - Campaign ID.
            'name': str - Campaign display name.
            'efficiency_score': float - Score from 0-100.
            'current_spend': float - Current spend.
            'suggested_spend': float - Recommended spend.
            'change': float - Dollar change from current.
            'change_pct': str - Percentage change (e.g., '+25.0%').
            'rationale': str - Explanation for the suggestion.
    """
    if not campaigns:
        return []

    # Filter to campaigns with actual spend data
    active = [c for c in campaigns if (c.get('cost_usd') or 0) > 0]
    if not active:
        print("  Warning: No campaigns with spend data for budget optimization.",
              file=sys.stderr)
        return []

    # Calculate total current spend if not provided
    current_total = sum(c.get('cost_usd') or 0 for c in active)
    if total_budget is None:
        total_budget = current_total

    if total_budget <= 0:
        print("  Warning: Total budget must be positive.", file=sys.stderr)
        return []

    # Find max values for normalization
    max_ctr = max((c.get('ctr') or 0) for c in active)
    max_cpc = max((c.get('cpc') or 0) for c in active)
    max_eng_rate = max((c.get('engagement_rate') or 0) for c in active)

    # Calculate efficiency scores
    scored = []
    for c in active:
        score = _calculate_efficiency_score(c, max_ctr, max_cpc, max_eng_rate)
        scored.append({
            'campaign': c,
            'score': score,
        })

    # Allocate budget proportionally to efficiency scores
    total_score = sum(s['score'] for s in scored)
    if total_score == 0:
        # Equal distribution if all scores are zero
        total_score = len(scored)
        for s in scored:
            s['score'] = 1

    results = []
    for s in scored:
        c = s['campaign']
        camp_name = c.get('display_name', c.get('name', f"Campaign {c.get('id', '?')}"))
        current_spend = c.get('cost_usd') or 0

        # Proportional allocation based on efficiency score
        proportion = s['score'] / total_score
        suggested = round(total_budget * proportion, 2)
        change = round(suggested - current_spend, 2)

        if current_spend > 0:
            change_pct = f'{(change / current_spend * 100):+.1f}%'
        elif suggested > 0:
            change_pct = '+100.0%'
        else:
            change_pct = '0.0%'

        # Generate rationale
        if change > 0:
            rationale = (
                f"Efficiency score {s['score']}/100. "
                f"Strong performance warrants increased investment. "
                f"CTR: {c.get('ctr', 0):.2f}%, "
                f"CPC: ${c.get('cpc', 0):.2f}."
            )
        elif change < 0:
            rationale = (
                f"Efficiency score {s['score']}/100. "
                f"Below-average efficiency suggests reallocating budget "
                f"to higher-performing campaigns. "
                f"CTR: {c.get('ctr', 0):.2f}%, "
                f"CPC: ${c.get('cpc', 0):.2f}."
            )
        else:
            rationale = (
                f"Efficiency score {s['score']}/100. "
                f"Current allocation is appropriate."
            )

        results.append({
            'id': c.get('id', ''),
            'name': camp_name,
            'efficiency_score': s['score'],
            'current_spend': round(current_spend, 2),
            'suggested_spend': suggested,
            'change': change,
            'change_pct': change_pct,
            'rationale': rationale,
        })

    # Sort by efficiency score descending
    results.sort(key=lambda r: r['efficiency_score'], reverse=True)

    return results
