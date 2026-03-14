"""
Page Classifier

Detects page type from URL structure AND performance metrics.
Gives different recommendations based on page type.
"""
import re


# ── URL-based classification ──
URL_PATTERNS = {
    'blog':       [r'/blog/', r'/article/', r'/post/', r'/news/', r'/guide/'],
    'product':    [r'/product/', r'/item/', r'/p/', r'/shop/', r'/buy/'],
    'category':   [r'/category/', r'/cat/', r'/collection/', r'/c/', r'/dept/'],
    'brand':      [r'/brand/', r'/brands/', r'/manufacturer/'],
    'sale':       [r'/sale/', r'/clearance/', r'/deals/', r'/discount/', r'/offer/'],
    'landing':    [r'/lp/', r'/landing/', r'/campaign/'],
    'homepage':   [r'^https?://[^/]+/?$'],
}


def classify_url(url: str) -> str:
    """Classify page type from URL structure"""
    url_lower = url.lower()
    for page_type, patterns in URL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return page_type
    return 'other'


def classify_performance(row) -> str:
    """
    Classify page performance from metrics.
    Returns one of: star, low_ctr, low_hanging, page2_trap,
                    zero_clicks, new_page, declining, normal
    """
    impressions = row.get('impressions', 0)
    clicks      = row.get('clicks', 0)
    ctr         = row.get('ctr', 0)
    position    = row.get('position', 99)

    from analyzers.ctr_curve import expected_ctr, ctr_performance_ratio
    exp_ctr = expected_ctr(position)
    ratio   = ctr_performance_ratio(ctr, position)

    if impressions < 100:
        return 'new_page'
    if clicks <= 3 and impressions >= 1000:
        return 'zero_clicks'
    if position <= 5 and ratio >= 1.1 and impressions >= 5000:
        return 'star'
    if position <= 8 and ratio < 0.5 and impressions >= 2000:
        return 'low_ctr'
    if 8 <= position <= 12 and impressions >= 2000:
        return 'low_hanging'
    if 11 <= position <= 20 and impressions >= 1500:
        return 'page2_trap'
    if ratio < 0.7 and impressions >= 1000:
        return 'declining'
    return 'normal'


def get_page_recommendations(url_type: str, perf_type: str, row: dict) -> list:
    """
    Return specific, actionable recommendations based on
    both URL type AND performance type.
    """
    position    = row.get('position', 0)
    ctr         = row.get('ctr', 0)
    impressions = row.get('impressions', 0)

    recs = []

    # ── Performance-based recommendations ──
    if perf_type == 'low_ctr':
        recs.append(f"Rewrite title tag — add a number, power word, or current year (CTR is {ctr:.1%} vs ~{row.get('expected_ctr', 0):.1%} expected at position #{int(position)})")
        recs.append("Improve meta description — add a clear benefit and call-to-action")
        recs.append("Check if a featured snippet is stealing your clicks (zero-click searches)")
        if url_type == 'product':
            recs.append("Add star rating schema markup to show review stars in search results")
        elif url_type == 'blog':
            recs.append("Add FAQ schema to earn expanded SERP real estate")

    elif perf_type == 'low_hanging':
        recs.append(f"Page is at position #{position:.1f} — just below page 1. A small push can 3x your clicks")
        recs.append("Add 3–5 internal links from high-traffic pages on your site")
        recs.append("Improve content depth — add 300–500 words covering related subtopics")
        recs.append("Update publish date and refresh any outdated statistics")
        if url_type == 'category':
            recs.append("Add keyword-rich category description text above the product grid")

    elif perf_type == 'page2_trap':
        recs.append(f"Position {position:.1f} — on page 2 with {impressions:,} impressions/month being wasted")
        recs.append("Conduct a content gap analysis — add sections covering questions competitors answer")
        recs.append("Build 2–3 quality backlinks from relevant sites")
        recs.append("Add internal links from your homepage and top category pages")

    elif perf_type == 'zero_clicks':
        recs.append("Page shows in search but nobody clicks — title/meta mismatch with user intent")
        recs.append("Research what users actually want for this query and rewrite accordingly")
        recs.append("Check Google Search Console for the actual queries triggering this page")

    elif perf_type == 'star':
        recs.append("Top performer — protect and maintain this page")
        recs.append("Add internal links FROM this page to boost other pages")
        recs.append("Consider expanding content to capture more related queries")

    # ── URL-type specific additions ──
    if url_type == 'product' and perf_type not in ('star',):
        recs.append("Ensure product schema (price, availability, reviews) is implemented")
    elif url_type == 'blog' and perf_type == 'low_hanging':
        recs.append("Add a table of contents and improve header structure for better UX signals")
    elif url_type == 'category' and perf_type == 'page2_trap':
        recs.append("Category pages need authoritative internal linking — link from homepage navigation")
    elif url_type == 'sale' and perf_type == 'low_ctr':
        recs.append("Sale pages need urgency in title — add '% Off', 'Today Only', or deal specifics")

    return recs[:4]  # Return top 4 most relevant recommendations