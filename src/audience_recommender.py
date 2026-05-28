"""
Generate targeting recommendations from demographic data.

Analyzes campaign demographics to identify high-performing and
low-performing audience segments, then suggests targeting changes
to improve overall campaign performance.
"""

import sys


# Minimum impressions for a segment to be considered in recommendations
MIN_SEGMENT_IMPRESSIONS = 50


def _analyze_demographic_segment(entries, segment_label):
    """Analyze a single demographic segment (e.g., industry, seniority).

    Args:
        entries: List of dicts with 'displayName', 'impressions', 'clicks'.
        segment_label: Human-readable segment name for recommendation text.

    Returns:
        List of recommendation dicts.
    """
    recommendations = []

    if not entries or len(entries) < 2:
        return recommendations

    # Calculate CTR for each entry
    analyzed = []
    total_imp = 0
    total_clk = 0
    for e in entries:
        imp = e.get('impressions') or 0
        clk = e.get('clicks') or 0
        name = e.get('displayName', e.get('pivotValue', 'Unknown'))
        total_imp += imp
        total_clk += clk
        if imp >= MIN_SEGMENT_IMPRESSIONS:
            ctr = (clk / imp * 100) if imp > 0 else 0
            analyzed.append({
                'name': name,
                'impressions': imp,
                'clicks': clk,
                'ctr': ctr,
            })

    if len(analyzed) < 2:
        return recommendations

    avg_ctr = (total_clk / total_imp * 100) if total_imp > 0 else 0

    # Sort by CTR descending
    analyzed.sort(key=lambda x: x['ctr'], reverse=True)

    # Identify top performers (CTR > 1.5x average)
    for entry in analyzed:
        if entry['ctr'] > avg_ctr * 1.5 and avg_ctr > 0:
            lift = ((entry['ctr'] - avg_ctr) / avg_ctr * 100) if avg_ctr else 0
            recommendations.append({
                'type': 'expand',
                'segment': segment_label,
                'target': entry['name'],
                'metric_ctr': round(entry['ctr'], 2),
                'benchmark_ctr': round(avg_ctr, 2),
                'impressions': entry['impressions'],
                'priority': 'high' if entry['ctr'] > avg_ctr * 2 else 'medium',
                'rationale': (
                    f"{entry['name']} has a CTR of {entry['ctr']:.2f}%, which is "
                    f"{lift:.0f}% above the segment average of {avg_ctr:.2f}%. "
                    f"Consider increasing budget allocation to this {segment_label.lower()}."
                ),
            })

    # Identify bottom performers (CTR < 0.5x average, with meaningful spend)
    for entry in analyzed:
        if entry['ctr'] < avg_ctr * 0.5 and avg_ctr > 0 and entry['impressions'] >= MIN_SEGMENT_IMPRESSIONS * 2:
            shortfall = ((avg_ctr - entry['ctr']) / avg_ctr * 100) if avg_ctr else 0
            recommendations.append({
                'type': 'reduce',
                'segment': segment_label,
                'target': entry['name'],
                'metric_ctr': round(entry['ctr'], 2),
                'benchmark_ctr': round(avg_ctr, 2),
                'impressions': entry['impressions'],
                'priority': 'high' if entry['ctr'] < avg_ctr * 0.25 else 'medium',
                'rationale': (
                    f"{entry['name']} has a CTR of {entry['ctr']:.2f}%, which is "
                    f"{shortfall:.0f}% below the segment average of {avg_ctr:.2f}%. "
                    f"Consider reducing or excluding this {segment_label.lower()} "
                    f"to improve overall efficiency."
                ),
            })

    return recommendations


def generate_recommendations(campaign_data):
    """Generate targeting recommendations from a campaign's demographic data.

    Analyzes the top-performing and bottom-performing demographics across
    industry, seniority, job function, company size, and geography segments.

    Args:
        campaign_data: A campaign dict as returned by LinkedInClient, containing
                       a 'demographics' dict with pivot data.

    Returns:
        List of recommendation dicts, each with keys:
            'type': str - 'expand' or 'reduce'.
            'segment': str - Demographic segment name.
            'target': str - Specific audience target.
            'metric_ctr': float - Target's CTR.
            'benchmark_ctr': float - Segment average CTR.
            'impressions': int - Impressions for this target.
            'priority': str - 'high' or 'medium'.
            'rationale': str - Human-readable explanation.
    """
    demographics = campaign_data.get('demographics', {})
    if not demographics:
        return []

    all_recommendations = []

    # Map pivot keys to human-readable labels
    segment_map = {
        'MEMBER_INDUSTRY': 'Industry',
        'MEMBER_SENIORITY': 'Seniority Level',
        'MEMBER_JOB_FUNCTION': 'Job Function',
        'MEMBER_JOB_TITLE': 'Job Title',
        'MEMBER_COMPANY_SIZE': 'Company Size',
        'MEMBER_COMPANY': 'Company',
        'MEMBER_REGION_V2': 'Region',
        'MEMBER_COUNTRY_V2': 'Country',
    }

    for pivot_key, label in segment_map.items():
        entries = demographics.get(pivot_key, [])
        if entries:
            recs = _analyze_demographic_segment(entries, label)
            all_recommendations.extend(recs)

    # Sort by priority (high first) then by CTR difference
    priority_order = {'high': 0, 'medium': 1}
    all_recommendations.sort(
        key=lambda r: (
            priority_order.get(r.get('priority', 'medium'), 2),
            -abs(r.get('metric_ctr', 0) - r.get('benchmark_ctr', 0)),
        )
    )

    if all_recommendations:
        expand_count = sum(1 for r in all_recommendations if r['type'] == 'expand')
        reduce_count = sum(1 for r in all_recommendations if r['type'] == 'reduce')
        camp_name = campaign_data.get('display_name', campaign_data.get('name', 'Unknown'))
        print(f"  Recommendations for {camp_name}: "
              f"{expand_count} expand, {reduce_count} reduce.",
              file=sys.stderr)

    return all_recommendations


def generate_all_recommendations(report_data):
    """Generate targeting recommendations for all campaigns in a report.

    Args:
        report_data: Dict with 'campaigns' list, as returned by
                     LinkedInClient.fetch_all_campaign_data().

    Returns:
        Dict mapping campaign ID to list of recommendations.
    """
    results = {}
    for campaign in report_data.get('campaigns', []):
        camp_id = campaign.get('id', '')
        recs = generate_recommendations(campaign)
        if recs:
            results[camp_id] = recs
    return results
