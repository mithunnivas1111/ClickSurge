"""
Cannibalization Analyzer

Finds cases where multiple pages compete for the same keyword,
splitting impressions and clicks — hurting overall rankings.
"""
import pandas as pd


class CannibalizationAnalyzer:
    def __init__(self, config):
        self.config = config
        self.threshold = config.get('cannibalization_threshold', 2)

    def find_cannibalization(self, df):
        """
        Find keywords where 2+ pages appear in search results.

        Args:
            df: DataFrame with columns: page, query, impressions, clicks, position

        Returns:
            DataFrame of cannibalization issues
        """
        if df is None or df.empty:
            return pd.DataFrame()

        required = {'page', 'query', 'impressions'}
        if not required.issubset(df.columns):
            return pd.DataFrame()

        # Group by query, count how many pages rank for each
        query_groups = df.groupby('query')
        issues = []

        for query, group in query_groups:
            if len(group) < self.threshold:
                continue  # Only 1 page — no cannibalization

            # Sort by impressions descending — best page first
            group_sorted = group.sort_values('impressions', ascending=False)
            total_impressions = group_sorted['impressions'].sum()
            total_clicks = group_sorted['clicks'].sum() if 'clicks' in group_sorted else 0
            page_count = len(group_sorted)

            # The dominant page (most impressions)
            dominant_page = group_sorted.iloc[0]['page']
            dominant_position = group_sorted.iloc[0].get('position', 'N/A')

            for _, row in group_sorted.iterrows():
                issues.append({
                    'page': row['page'],
                    'query': query,
                    'issue_type': 'Keyword Cannibalization',
                    'priority': 'High' if page_count >= 3 else 'Medium',
                    'impressions': row['impressions'],
                    'clicks': row.get('clicks', 0),
                    'position': row.get('position', 0),
                    'ctr': row.get('ctr', 0),
                    'competing_pages': page_count,
                    'dominant_page': dominant_page,
                    'total_query_impressions': total_impressions,
                    'estimated_gain': int(total_impressions * 0.04),
                    'action': (
                        f"HIGH PRIORITY: {page_count} pages splitting traffic for '{query}'. "
                        f"Consolidate content into '{dominant_page}'. "
                        f"301-redirect or noindex the weaker pages. "
                        f"Add canonical tags pointing to the dominant page."
                    )
                })

        if not issues:
            return pd.DataFrame()

        result = pd.DataFrame(issues)
        result = result.drop_duplicates(subset=['page', 'query'])
        result = result.sort_values('total_query_impressions', ascending=False)
        return result
