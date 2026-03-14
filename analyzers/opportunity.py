"""
Opportunity Analyzer

Merges all detected issues, applies opportunity scoring,
and produces a ranked report sorted by highest traffic gain.
"""
import pandas as pd


class OpportunityAnalyzer:
    def __init__(self, config):
        self.config = config

    def create_opportunity_report(self, gsc_issues, cannibalization):
        all_opps = []

        if gsc_issues is not None and not gsc_issues.empty:
            gsc_clean = gsc_issues.copy()
            gsc_clean['type'] = gsc_clean.get('issue_type', 'Page Optimization')
            all_opps.append(gsc_clean)

        if cannibalization is not None and not cannibalization.empty:
            cannib_clean = cannibalization.copy()
            cannib_clean['type'] = 'Keyword Cannibalization'
            all_opps.append(cannib_clean)

        if not all_opps:
            return pd.DataFrame()

        combined = pd.concat(all_opps, ignore_index=True)

        for col in ['estimated_gain', 'priority', 'action', 'page']:
            if col not in combined.columns:
                combined[col] = '' if col in ('action', 'page') else 0

        # Priority score for sorting
        combined['priority_score'] = combined['priority'].map(
            {'High': 3, 'Medium': 2, 'Low': 1}
        ).fillna(1)

        # Final sort: opportunity_score if available, else estimated_gain
        if 'opportunity_score' in combined.columns:
            combined = combined.sort_values(
                ['priority_score', 'opportunity_score', 'estimated_gain'],
                ascending=[False, False, False]
            )
        else:
            combined = combined.sort_values(
                ['priority_score', 'estimated_gain'],
                ascending=[False, False]
            )

        combined = combined.reset_index(drop=True)
        combined['rank'] = combined.index + 1
        return combined

    def get_quick_wins(self, opportunities, limit=10):
        if opportunities.empty:
            return pd.DataFrame()
        quick = opportunities[opportunities['priority'].isin(['High', 'Medium'])]
        if 'opportunity_score' in quick.columns:
            quick = quick.sort_values('opportunity_score', ascending=False)
        else:
            quick = quick.sort_values('estimated_gain', ascending=False)
        return quick.head(limit).reset_index(drop=True)

    def get_summary_stats(self, opportunities):
        if opportunities.empty:
            return {
                'total_opportunities': 0,
                'high_priority': 0,
                'medium_priority': 0,
                'low_priority': 0,
                'total_estimated_gain': 0,
                'page_optimization_count': 0,
                'cannibalization_count': 0,
                'avg_ctr_gap': 0,
            }

        avg_ctr_gap = 0
        if 'expected_ctr' in opportunities.columns and 'ctr' in opportunities.columns:
            gaps = opportunities['expected_ctr'] - opportunities['ctr']
            avg_ctr_gap = round(gaps.mean(), 4)

        return {
            'total_opportunities':    len(opportunities),
            'high_priority':          len(opportunities[opportunities['priority'] == 'High']),
            'medium_priority':        len(opportunities[opportunities['priority'] == 'Medium']),
            'low_priority':           len(opportunities[opportunities['priority'] == 'Low']),
            'total_estimated_gain':   int(opportunities['estimated_gain'].sum()),
            'page_optimization_count': len(opportunities[opportunities['type'] != 'Keyword Cannibalization']),
            'cannibalization_count':  len(opportunities[opportunities['type'] == 'Keyword Cannibalization']),
            'avg_ctr_gap':            avg_ctr_gap,
        }