"""
AI-powered insights using Ollama (free, local) with fallback to Claude/OpenAI.
Ollama runs on localhost:11434 with OpenAI-compatible API.
"""

import os
import json
import requests
import sys


def _try_ollama(prompt, model=None):
    """Try generating insights via local Ollama instance."""
    model = model or os.environ.get('OLLAMA_MODEL', 'llama3.1')
    base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

    try:
        resp = requests.post(
            f'{base_url}/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.7, 'num_predict': 1500}
            },
            timeout=120
        )
        if resp.status_code == 200:
            return resp.json().get('response', '')
    except Exception as e:
        print(f"  Ollama not available: {e}", file=sys.stderr)
    return None


def _try_anthropic(prompt):
    """Try generating insights via Claude API."""
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        model = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"  Claude API not available: {e}", file=sys.stderr)
    return None


def _try_openai(prompt):
    """Try generating insights via OpenAI API."""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  OpenAI API not available: {e}", file=sys.stderr)
    return None


def _build_campaign_summary(campaigns):
    """Build a text summary of campaign data for the AI prompt."""
    lines = []
    total_imp = sum(c.get('impressions', 0) for c in campaigns)
    total_clicks = sum(c.get('clicks', 0) for c in campaigns)
    total_spend = sum(float(c.get('cost_usd', 0) or 0) for c in campaigns)
    total_eng = sum(c.get('engagements', 0) for c in campaigns)
    overall_ctr = (total_clicks / total_imp * 100) if total_imp > 0 else 0

    lines.append(f"OVERALL: {len(campaigns)} campaigns, {total_imp:,} impressions, {total_clicks:,} clicks, CTR {overall_ctr:.2f}%, ${total_spend:,.2f} spend, {total_eng:,} engagements")
    lines.append("")

    for c in campaigns:
        name = c.get('display_name', c.get('name', 'Unknown'))
        imp = c.get('impressions', 0)
        clicks = c.get('clicks', 0)
        ctr = float(c.get('ctr', 0) or 0)
        spend = float(c.get('cost_usd', 0) or 0)
        eng = c.get('engagements', 0)
        likes = c.get('likes', 0)
        comments = c.get('comments', 0)
        shares = c.get('shares', 0)
        viral_imp = c.get('viral_impressions', 0)
        video_views = c.get('video_views', 0)
        leads = c.get('oneClickLeads', 0) or c.get('one_click_leads', 0) or 0

        line = f"- {name}: {imp:,} imp, {clicks:,} clicks, {ctr:.2f}% CTR, ${spend:,.2f} spend"
        line += f", {eng:,} engagements, {likes} likes, {comments} comments, {shares} shares"
        if viral_imp:
            line += f", {viral_imp:,} viral impressions"
        if video_views:
            line += f", {video_views:,} video views"
        if leads:
            line += f", {leads} leads"

        # Add top demographics if available
        demos = c.get('demographics', {})
        if demos.get('MEMBER_INDUSTRY'):
            top_ind = sorted(demos['MEMBER_INDUSTRY'], key=lambda x: x.get('impressions', 0), reverse=True)[:3]
            ind_names = [i.get('displayName', '?') for i in top_ind]
            line += f" | Top industries: {', '.join(ind_names)}"
        if demos.get('MEMBER_SENIORITY'):
            top_sen = sorted(demos['MEMBER_SENIORITY'], key=lambda x: x.get('impressions', 0), reverse=True)[:3]
            sen_names = [s.get('displayName', '?') for s in top_sen]
            line += f" | Top seniority: {', '.join(sen_names)}"

        lines.append(line)

    return "\n".join(lines)


def generate_insights(campaigns):
    """
    Generate AI-powered insights from campaign data.

    Tries: Ollama (free) -> Claude API -> OpenAI API -> returns empty list

    Returns:
        list of dicts: [{"title": "...", "insight": "...", "recommendation": "..."}, ...]
    """
    summary = _build_campaign_summary(campaigns)

    prompt = f"""You are a senior LinkedIn Ads strategist. Analyze these LinkedIn ad campaign performance metrics and provide exactly 5 strategic insights.

CAMPAIGN DATA:
{summary}

LINKEDIN 2026 BENCHMARKS:
- Average CTR: 0.44-0.65%
- Average CPC: $5.58
- Average CPM: $33.80
- Video engagement rate: 1.6%
- Lead gen form completion: 10%
- Average conversion rate: 6.1%

For each insight, provide:
1. A short title (5-8 words)
2. The insight explanation (2-3 sentences with specific numbers from the data)
3. A concrete actionable recommendation (1-2 sentences)

Format your response as JSON array:
[
  {{"title": "...", "insight": "...", "recommendation": "..."}},
  ...
]

Return ONLY the JSON array, no other text."""

    # Try each provider in order
    response = _try_ollama(prompt)
    if not response:
        response = _try_anthropic(prompt)
    if not response:
        response = _try_openai(prompt)
    if not response:
        return []

    # Parse JSON from response
    try:
        # Try to find JSON array in the response
        text = response.strip()
        # Find first [ and last ]
        start = text.find('[')
        end = text.rfind(']')
        if start >= 0 and end > start:
            json_str = text[start:end+1]
            insights = json.loads(json_str)
            if isinstance(insights, list):
                return insights[:5]
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  Could not parse AI response as JSON: {e}", file=sys.stderr)

    return []


def generate_executive_summary(campaigns):
    """Generate a 3-sentence executive summary."""
    summary = _build_campaign_summary(campaigns)

    prompt = f"""You are a senior LinkedIn Ads strategist. Write a 3-sentence executive summary for this LinkedIn ad campaign report.

CAMPAIGN DATA:
{summary}

Write exactly 3 sentences:
1. Overall performance summary with key numbers
2. The standout finding (best/worst performer, notable trend)
3. The single most important recommendation

Be specific, use actual numbers from the data. Keep it concise and professional. Return only the 3 sentences, nothing else."""

    response = _try_ollama(prompt)
    if not response:
        response = _try_anthropic(prompt)
    if not response:
        response = _try_openai(prompt)

    return response.strip() if response else ''


def generate_campaign_recommendation(campaign):
    """Generate a specific recommendation for a single campaign."""
    name = campaign.get('display_name', campaign.get('name', 'Unknown'))
    imp = campaign.get('impressions', 0)
    clicks = campaign.get('clicks', 0)
    ctr = float(campaign.get('ctr', 0) or 0)
    spend = float(campaign.get('cost_usd', 0) or 0)

    prompt = f"""As a LinkedIn Ads strategist, give ONE specific recommendation for this campaign in 2 sentences:
Campaign: {name}
Impressions: {imp:,}, Clicks: {clicks:,}, CTR: {ctr:.2f}%, Spend: ${spend:,.2f}
LinkedIn avg CTR: 0.44-0.65%, avg CPC: $5.58

Return only the recommendation, nothing else."""

    response = _try_ollama(prompt)
    if not response:
        response = _try_anthropic(prompt)
    if not response:
        response = _try_openai(prompt)

    return response.strip() if response else ''


def check_ollama_available():
    """Check if Ollama is running and accessible."""
    base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    try:
        resp = requests.get(f'{base_url}/api/tags', timeout=5)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            return True, model_names
    except Exception:
        pass
    return False, []
