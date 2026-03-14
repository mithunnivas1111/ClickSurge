#!/usr/bin/env python3
"""
CSV Analysis Mode

Analyze SEO data from a CSV file instead of Google Search Console.
Useful for:
- Testing with sample data
- Analyzing client-provided data
- Working with exported data from other tools

Usage:
    python analyze_csv.py your_data.csv
"""

import sys
import pandas as pd
from datetime import datetime

from utils.logger import setup_logger
from utils.helpers import ensure_output_folder
from analyzers.gsc_analyzer import GSCAnalyzer
from analyzers.opportunity import OpportunityAnalyzer

logger = setup_logger(__name__)

def main():
    # Check if CSV file provided
    if len(sys.argv) < 2:
        print("=" * 60)
        print("CSV ANALYSIS MODE")
        print("=" * 60)
        print()
        print("Usage:")
        print("  python analyze_csv.py your_data.csv")
        print()
        print("CSV file must have these columns:")
        print("  - page         (URL)")
        print("  - impressions  (number)")
        print("  - clicks       (number)")
        print("  - ctr          (decimal, e.g., 0.05 for 5%)")
        print("  - position     (average position, e.g., 5.5)")
        print()
        print("Example CSV:")
        print("  page,impressions,clicks,ctr,position")
        print("  https://example.com/page1,5000,100,0.02,5.5")
        print("  https://example.com/page2,3000,120,0.04,3.2")
        print()
        return 1
    
    csv_file = sys.argv[1]
    
    print("=" * 60)
    print("SEO ANALYTICS - CSV MODE")
    print("=" * 60)
    print()
    
    try:
        # Load CSV
        print(f"📂 Loading data from: {csv_file}")
        data = pd.read_csv(csv_file)
        
        # Validate required columns
        required_cols = ['page', 'impressions', 'clicks', 'ctr', 'position']
        missing_cols = [col for col in required_cols if col not in data.columns]
        
        if missing_cols:
            print(f"\n❌ Error: Missing required columns: {missing_cols}")
            print(f"\nYour columns: {list(data.columns)}")
            print(f"\nRequired: {required_cols}")
            return 1
        
        print(f"✅ Loaded {len(data)} pages\n")
        
        # Configuration
        config = {
            'min_impressions': 100,
            'low_ctr_threshold': 0.02,
            'high_impression_threshold': 1000,
            'output_folder': 'reports'
        }
        
        # Run analysis
        print("🔍 Analyzing SEO performance...")
        
        analyzer = GSCAnalyzer(config)
        issues = analyzer.analyze_all(data)
        
        if issues.empty:
            print("\n✅ No major issues found!")
            print("   Consider lowering thresholds in the script if you want deeper analysis.")
            return 0
        
        # Create opportunity report
        opp_analyzer = OpportunityAnalyzer(config)
        opportunities = opp_analyzer.create_opportunity_report(issues, pd.DataFrame())
        
        # Summary
        summary = opp_analyzer.get_summary_stats(opportunities)
        
        print()
        print("=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total Opportunities: {summary['total_opportunities']}")
        print(f"  🔴 High Priority:   {summary['high_priority']}")
        print(f"  🟡 Medium Priority: {summary['medium_priority']}")
        print(f"  🟢 Low Priority:    {summary['low_priority']}")
        print()
        print(f"📈 Estimated Gain: +{int(summary['total_estimated_gain'])} clicks/month")
        print("=" * 60)
        print()
        
        # Top opportunities
        quick_wins = opp_analyzer.get_quick_wins(opportunities, limit=5)
        
        if not quick_wins.empty:
            print("TOP 5 QUICK WINS")
            print("-" * 60)
            
            for _, opp in quick_wins.iterrows():
                print(f"\n#{opp['rank']} - {opp['type']} [{opp['priority']}]")
                print(f"   Page: {opp['page']}")
                print(f"   Gain: +{int(opp['estimated_gain'])} clicks/month")
                print(f"   Action: {opp['action']}")
            
            print("\n" + "-" * 60)
            print()
        
        # Save results
        ensure_output_folder(config['output_folder'])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = f"{config['output_folder']}/CSV_analysis_{timestamp}.csv"
        opportunities.to_csv(output_file, index=False)
        
        print(f"💾 Report saved: {output_file}")
        print()
        
        return 0
        
    except FileNotFoundError:
        print(f"\n❌ Error: File not found: {csv_file}")
        return 1
    except pd.errors.EmptyDataError:
        print(f"\n❌ Error: CSV file is empty")
        return 1
    except Exception as e:
        logger.error(f"Error analyzing CSV: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
