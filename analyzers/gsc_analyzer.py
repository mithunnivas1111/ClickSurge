"""
GSC Analyzer — Position-aware issue detection using CTR curve model.

Every issue is now detected relative to EXPECTED CTR at that position,
not a fixed threshold. This gives accurate, realistic issue detection.
"""
import pandas as pd
from analyzers.ctr_curve import expected_ctr, ctr_performance_ratio, opportunity_clicks
from analyzers.page_classifier import classify_url, classify_performance, get_page_recommendations


class GSCAnalyzer:
    def __init__(self, config):
        self.config = config
        self.min_impressions           = config.get('min_impressions', 500)
        self.high_impression_threshold = config.get('high_impression_threshold', 3000)
        # CTR ratio threshold: flag if actual CTR < X * expected CTR
        self.low_ctr_ratio             = config.get('low_ctr_ratio', 0.55)

    # ────────────────────────────────────────────
    # 1. LOW CTR — position-aware detection
    # ────────────────────────────────────────────
    def find_low_ctr_pages(self, df):
        """
        Flag pages where actual CTR < 55% of expected CTR for their position.
        Only for pages with meaningful impressions in positions 1–10.
        """
        def is_low_ctr(row):
            if row['impressions'] < self.high_impression_threshold:
                return False
            if row['position'] > 10:
                return False
            ratio = ctr_performance_ratio(row['ctr'], row['position'])
            return ratio < self.low_ctr_ratio

        mask    = df.apply(is_low_ctr, axis=1)
        results = df[mask].copy()
        if results.empty:
            return results

        results['expected_ctr']   = results['position'].apply(expected_ctr)
        results['ctr_ratio']      = results.apply(
            lambda r: ctr_performance_ratio(r['ctr'], r['position']), axis=1
        )
        results['issue_type'] = 'Low CTR'
        results['priority']   = results.apply(
            lambda r: 'High' if (r['impressions'] >= 8000 and r['position'] <= 5) else 'Medium',
            axis=1
        )
        results['estimated_gain'] = results.apply(
            lambda r: opportunity_clicks(int(r['impressions']), r['ctr'], r['position']), axis=1
        )
        results['action'] = results.apply(self._low_ctr_action, axis=1)
        return results

    # ────────────────────────────────────────────
    # 2. LOW HANGING FRUIT — positions 8–12
    # ────────────────────────────────────────────
    def find_low_hanging_fruit(self, df):
        """
        Pages ranking 8–12 with high impressions.
        A small content or link push can bring them to top 5.
        """
        mask = (
            (df['impressions'] >= self.high_impression_threshold) &
            (df['position'] >= 8) &
            (df['position'] <= 12)
        )
        results = df[mask].copy()
        if results.empty:
            return results

        results['expected_ctr']   = results['position'].apply(expected_ctr)
        results['issue_type'] = 'Low Hanging Fruit'
        results['priority']   = results['impressions'].apply(
            lambda x: 'High' if x >= 10000 else 'Medium'
        )
        # Gain = what they'd earn at position 5 vs current
        results['estimated_gain'] = results.apply(
            lambda r: max(0, int(r['impressions'] * (0.061 - expected_ctr(r['position'])))),
            axis=1
        )
        results['action'] = results.apply(
            lambda r: (
                f"Ranked #{r['position']:.1f} with {int(r['impressions']):,} impressions/mo — "
                f"just below page 1. Expected CTR here is only {expected_ctr(r['position']):.1%}. "
                f"Pushing to top 5 adds ~{r['estimated_gain']:,} clicks/mo. "
                "Add internal links, refresh content, and target related keywords."
            ), axis=1
        )
        return results

    # ────────────────────────────────────────────
    # 3. ZERO CLICKS
    # ────────────────────────────────────────────
    def find_zero_click_pages(self, df):
        """
        Pages with significant impressions but near-zero clicks.
        """
        mask = (
            (df['impressions'] >= 2000) &
            (df['clicks'] <= 5)
        )
        results = df[mask].copy()
        if results.empty:
            return results

        results['expected_ctr']   = results['position'].apply(expected_ctr)
        results['issue_type'] = 'Zero Clicks'
        results['priority']   = results['impressions'].apply(
            lambda x: 'High' if x >= 6000 else 'Medium'
        )
        results['estimated_gain'] = results.apply(
            lambda r: int(r['impressions'] * expected_ctr(r['position']) * 0.5), axis=1
        )
        results['action'] = results.apply(
            lambda r: (
                f"{int(r['impressions']):,} impressions but only {int(r['clicks'])} clicks. "
                f"At position #{r['position']:.1f} you should expect ~{expected_ctr(r['position']):.1%} CTR. "
                "Title/meta description is not matching user intent. "
                "Rewrite title to directly answer the search query."
            ), axis=1
        )
        return results

    # ────────────────────────────────────────────
    # 4. PAGE 2 TRAP — positions 11–15
    # ────────────────────────────────────────────
    def find_page2_pages(self, df):
        """
        High-impression pages stuck on page 2.
        Moving to page 1 (pos 8-10) gives 3–5× more clicks.
        """
        mask = (
            (df['impressions'] >= self.high_impression_threshold * 1.5) &
            (df['position'] > 10) &
            (df['position'] <= 15)
        )
        results = df[mask].copy()
        if results.empty:
            return results

        results['expected_ctr']   = results['position'].apply(expected_ctr)
        results['issue_type'] = 'Page 2 Trap'
        results['priority']   = results['impressions'].apply(
            lambda x: 'High' if x >= 12000 else 'Medium'
        )
        # Gain vs moving to position 8
        results['estimated_gain'] = results.apply(
            lambda r: max(0, int(r['impressions'] * (0.032 - expected_ctr(r['position'])))),
            axis=1
        )
        results['action'] = results.apply(
            lambda r: (
                f"Position #{r['position']:.1f} — on page 2 with {int(r['impressions']):,} monthly impressions wasted. "
                f"Current CTR {r['ctr']:.1%} vs {0.032:.1%} if on page 1. "
                "Strengthen content depth, add internal links from authority pages, build 2–3 backlinks."
            ), axis=1
        )
        return results

    # ────────────────────────────────────────────
    # HELPERS
    # ────────────────────────────────────────────
    def _low_ctr_action(self, row):
        pos      = row['position']
        ctr      = row['ctr']
        exp      = row['expected_ctr']
        ratio    = row['ctr_ratio']
        gap      = exp - ctr
        gain     = row['estimated_gain']
        url_type = classify_url(row.get('page', ''))

        base = (
            f"Position #{pos:.1f}: actual CTR {ctr:.1%} vs {exp:.1%} expected "
            f"({ratio:.0%} of benchmark). Fixing could add +{gain:,} clicks/mo. "
        )
        if pos <= 3:
            base += "CRITICAL: Top 3 but low CTR. Rewrite title with number/power word. Add FAQ schema."
        elif pos <= 6:
            base += "Rewrite title tag. A/B test with numbers and current year. Add structured data."
        else:
            base += "Improve title relevance. Ensure meta description matches search intent exactly."

        if url_type == 'product':
            base += " Add review schema for star ratings in SERPs."
        elif url_type == 'blog':
            base += " Add FAQ schema for expanded SERP presence."
        elif url_type == 'sale':
            base += " Add urgency/discount % to title tag."
        return base

    # ────────────────────────────────────────────
    # MAIN — run all checks
    # ────────────────────────────────────────────
    def analyze_all(self, df):
        all_issues = []
        for check in [
            self.find_low_ctr_pages,
            self.find_low_hanging_fruit,
            self.find_zero_click_pages,
            self.find_page2_pages,
        ]:
            result = check(df)
            if not result.empty:
                all_issues.append(result)

        if not all_issues:
            return pd.DataFrame()

        combined = pd.concat(all_issues, ignore_index=True)
        combined = combined.drop_duplicates(subset=['page', 'issue_type'])

        # Add URL type classification
        combined['url_type'] = combined['page'].apply(classify_url)

        # Opportunity score = weighted by impressions + CTR gap + position value
        combined['opportunity_score'] = combined.apply(
            lambda r: round(
                r['impressions'] * (1 - r.get('ctr_ratio', 0.5)) * (1 / max(r['position'], 1)), 2
            ), axis=1
        )

        # Sort by opportunity score
        combined = combined.sort_values('opportunity_score', ascending=False)
        combined = combined.head(150)  # Cap at top 150
        combined = combined.reset_index(drop=True)
        return combined