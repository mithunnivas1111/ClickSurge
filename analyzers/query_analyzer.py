"""
QueryAnalyzer
=============
Analyses the GSC Queries CSV and combines it with the Pages CSV.

Since GSC exports queries and pages separately (no page+query joint export),
this module:
  1. Analyses query-level CTR/position issues independently
  2. Matches each query → its most likely serving page via URL keyword overlap
  3. Produces a combined DataFrame with both query metrics + page metrics side-by-side
  4. Runs a gap analysis: queries ranking in top-10 but with low CTR
"""

import re
import pandas as pd
from analyzers.ctr_curve import expected_ctr, ctr_performance_ratio


# Stop-words to ignore when matching query terms → URL slugs
_STOP = {
    '', 'the', 'and', 'for', 'in', 'of', 'to', 'a', 'an', 'on', 'at',
    'by', 'is', 'are', 'was', 'accessories', 'india', 'online', 'best',
    'buy', 'near', 'me', 'shop',
}


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _slug_keywords(url: str) -> set:
    """Extract meaningful keywords from a page URL slug."""
    slug = url.lower()
    # Strip domain
    slug = re.sub(r'https?://[^/]+', '', slug)
    # Strip common path prefixes
    for prefix in ['collections/', 'categories/', 'products/', 'product-details/', 'blog/']:
        slug = slug.replace(prefix, ' ')
    # Tokenise on non-alpha
    tokens = re.split(r'[^a-z0-9]+', slug)
    return set(tokens) - _STOP


def _query_keywords(query: str) -> set:
    """Tokenise a search query, remove stop-words."""
    return set(query.lower().split()) - _STOP


def _classify_query_issue(row) -> str | None:
    """Return the issue label for a query row, or None if no issue."""
    pos   = row['q_position']
    ratio = row['q_ctr_ratio']
    imp   = row['q_impressions']
    clk   = row['q_clicks']

    if imp >= 1000 and ratio < 0.40 and pos <= 10:
        return 'Low CTR Query'
    if 8 <= pos <= 12 and imp >= 500:
        return 'Low Hanging Query'
    if pos <= 15 and imp >= 2000 and clk <= 10:
        return 'Zero Click Query'
    if 11 <= pos <= 20 and imp >= 500:
        return 'Page 2 Query'
    return None


def _priority(issue: str | None, ratio: float, imp: int) -> str:
    if issue in ('Low CTR Query', 'Zero Click Query') and imp >= 5000:
        return 'High'
    if issue in ('Low CTR Query', 'Low Hanging Query') and imp >= 1000:
        return 'Medium'
    if issue is not None:
        return 'Low'
    return ''


def _action(issue: str | None, query: str, pos: float) -> str:
    if issue == 'Low CTR Query':
        return (f'Query "{query}" ranks #{pos:.1f} but CTR is far below benchmark. '
                'Rewrite the title tag of the serving page to include this exact query. '
                'Add emotional triggers, numbers, or a clear benefit promise.')
    if issue == 'Low Hanging Query':
        return (f'Query "{query}" is at position #{pos:.1f} — one push could reach page 1. '
                'Add this query to the H1 and first paragraph. Build 2–3 internal links to the page.')
    if issue == 'Zero Click Query':
        return (f'Query "{query}" gets {pos:.1f} position impressions but nearly zero clicks. '
                'The SERP likely shows a featured snippet or knowledge panel stealing clicks. '
                'Target a different long-tail variant, or optimise for the snippet itself.')
    if issue == 'Page 2 Query':
        return (f'Query "{query}" is stuck on page 2 (#{pos:.1f}). '
                'Improve page speed, add more internal links, and deepen the content '
                'to overtake the top-10 results.')
    return ''


# ──────────────────────────────────────────────────────────────────────────────
#  Main Class
# ──────────────────────────────────────────────────────────────────────────────

class QueryAnalyzer:
    """
    Combines the GSC Queries export with the Pages export.
    Expected columns after normalisation:
      - queries_df : query, impressions, clicks, ctr, position
      - pages_df   : page,  impressions, clicks, ctr, position
    """

    def __init__(self, config: dict):
        self.min_impressions = config.get('min_impressions', 100)
        self.high_imp_threshold = config.get('high_impression_threshold', 3000)

    # ── Step 1: Enrich queries with CTR benchmark ────────────────────────────

    def _enrich_queries(self, queries_df: pd.DataFrame) -> pd.DataFrame:
        df = queries_df.copy()
        df.columns = [c.lower().strip() for c in df.columns]
        # Rename 'query' if it's still 'top queries'
        if 'top queries' in df.columns:
            df = df.rename(columns={'top queries': 'query'})

        df['q_impressions'] = df['impressions'].astype(int)
        df['q_clicks']      = df['clicks'].astype(int)
        df['q_ctr']         = df['ctr'].astype(float)
        df['q_position']    = df['position'].astype(float)
        df['q_expected_ctr']= df['q_position'].apply(expected_ctr)
        df['q_ctr_ratio']   = df.apply(
            lambda r: ctr_performance_ratio(r['q_ctr'], r['q_position']), axis=1)
        df['q_opportunity_clicks'] = (
            (df['q_expected_ctr'] * 0.85 - df['q_ctr']) * df['q_impressions']
        ).clip(lower=0).round(0).astype(int)

        df['q_issue']    = df.apply(_classify_query_issue, axis=1)
        df['q_priority'] = df.apply(
            lambda r: _priority(r['q_issue'], r['q_ctr_ratio'], r['q_impressions']), axis=1)
        df['q_action']   = df.apply(
            lambda r: _action(r['q_issue'], r['query'], r['q_position']), axis=1)
        return df

    # ── Step 2: Build page slug keyword index ───────────────────────────────

    def _build_page_index(self, pages_df: pd.DataFrame) -> pd.DataFrame:
        df = pages_df.copy()
        df.columns = [c.lower().strip() for c in df.columns]
        df['_kws'] = df['page'].apply(_slug_keywords)
        return df

    # ── Step 3: Match each query → best page ────────────────────────────────

    def _match_query_to_page(self, query: str, page_index: pd.DataFrame) -> dict | None:
        q_kws = _query_keywords(query)
        if not q_kws:
            return None

        best_score = 0
        best_row   = None
        for _, row in page_index.iterrows():
            overlap = len(q_kws & row['_kws'])
            if overlap > best_score or (
                overlap == best_score and best_row is not None and
                row['impressions'] > best_row['impressions']
            ):
                best_score = overlap
                best_row   = row

        if best_score == 0 or best_row is None:
            return None

        return {
            'matched_page':         best_row['page'],
            'page_impressions':     int(best_row['impressions']),
            'page_clicks':          int(best_row['clicks']),
            'page_ctr':             float(best_row['ctr']),
            'page_position':        float(best_row['position']),
            'match_confidence':     best_score,
        }

    # ── Public API ───────────────────────────────────────────────────────────

    def analyze(self, queries_df: pd.DataFrame, pages_df: pd.DataFrame | None) -> pd.DataFrame:
        """
        Returns a combined DataFrame with:
          - All query metrics (q_*)
          - Matched page metrics (page_*)
          - Issue classification + priority + action
        """
        enriched    = self._enrich_queries(queries_df)
        page_index  = self._build_page_index(pages_df) if pages_df is not None else None

        if page_index is not None:
            matches = enriched['query'].apply(
                lambda q: self._match_query_to_page(q, page_index))
            # Replace None with empty dicts so DataFrame construction works
            match_df = pd.DataFrame(
                [m if m is not None else {} for m in matches.tolist()]
            )
            combined = pd.concat([enriched.reset_index(drop=True),
                                   match_df.reset_index(drop=True)], axis=1)
        else:
            combined = enriched.copy()
            for col in ['matched_page','page_impressions','page_clicks',
                        'page_ctr','page_position','match_confidence']:
                combined[col] = None

        # Keep only relevant cols in clean order
        base_cols = [
            'query', 'q_impressions', 'q_clicks', 'q_ctr', 'q_position',
            'q_expected_ctr', 'q_ctr_ratio', 'q_opportunity_clicks',
            'q_issue', 'q_priority', 'q_action',
            'matched_page', 'page_impressions', 'page_clicks',
            'page_ctr', 'page_position', 'match_confidence',
        ]
        return combined[[c for c in base_cols if c in combined.columns]].reset_index(drop=True)

    def get_query_issues(self, combined_df: pd.DataFrame) -> pd.DataFrame:
        """Return only rows that have a detected issue, sorted by opportunity."""
        return (combined_df[combined_df['q_issue'].notna()]
                .sort_values(['q_priority', 'q_opportunity_clicks'],
                             ascending=[True, False])
                .reset_index(drop=True))

    def get_gap_analysis(self, combined_df: pd.DataFrame) -> pd.DataFrame:
        """
        Gap analysis: queries in top-10 with decent impressions but low CTR.
        These are the highest-ROI title/meta rewrites.
        """
        if combined_df.empty:
            return pd.DataFrame()
        mask = (
            (combined_df['q_position'] <= 10) &
            (combined_df['q_ctr_ratio'] < 0.55) &
            (combined_df['q_impressions'] >= self.min_impressions)
        )
        return (combined_df[mask]
                .sort_values('q_opportunity_clicks', ascending=False)
                .reset_index(drop=True))

    def get_summary_stats(self, combined_df: pd.DataFrame) -> dict:
        issues = combined_df[combined_df['q_issue'].notna()]
        return {
            'total_queries':      len(combined_df),
            'total_issues':       len(issues),
            'high_priority':      len(issues[issues['q_priority'] == 'High']),
            'medium_priority':    len(issues[issues['q_priority'] == 'Medium']),
            'total_opp_clicks':   int(issues['q_opportunity_clicks'].sum()),
            'matched_queries':    int(combined_df['matched_page'].notna().sum()),
            'avg_position':       round(combined_df['q_position'].mean(), 1),
            'avg_ctr':            round(combined_df['q_ctr'].mean(), 4),
        }