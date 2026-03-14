#!/usr/bin/env python3
"""
SEO Analytics System - DEMO MODE

This version works with demo data instead of real Google Search Console.
Perfect for testing the system without GSC access.

Usage:
    1. python demo_data.py       (generates demo data)
    2. python main_demo.py        (runs analysis on demo data)
"""

import sys
import pandas as pd
from datetime import datetime

from utils.logger import setup_logger
from utils.helpers import ensure_output_folder
from analyzers.gsc_analyzer import GSCAnalyzer
from analyzers.cannibalization import CannibalizationAnalyzer
from analyzers.opportunity import OpportunityAnalyzer

# Setup logging
logger = setup_logger(__name__)

def main():
    """Main execution function for demo mode"""
    
    print("=" * 60)
    print("SEO ANALYTICS SYSTEM - DEMO MODE")
    print("Testing with Simulated Data")
    print("=" * 60)
    print()
    
    # Demo configuration
    config = {
        'site_url': 'https://demo-store.com',
        'min_impressions': 100,
        'low_ctr_threshold': 0.02,
        'cannibalization_threshold': 2,
        'high_impression_threshold': 1000,
        'output_folder': 'reports'
    }
    
    try:
        # Step 1: Load demo data
        logger.info("Loading demo data...")
        print("📂 Loading demo Search Console data...")
        
        try:
            page_data = pd.read_csv('demo_page_data.csv')
            page_query_data = pd.read_csv('demo_page_query_data.csv')
            
            print(f"✅ Loaded {len(page_data)} pages")
            print(f"✅ Loaded {len(page_query_data)} page-keyword combinations\n")
            
        except FileNotFoundError:
            print("\n❌ Demo data files not found!")
            print("\nPlease run this first:")
            print("  python demo_data.py")
            print("\nThis will generate the demo data files.\n")
            return 1
        
        # Step 2: Run analyses
        print("🔍 Analyzing SEO performance...\n")
        
        # Initialize analyzers
        gsc_analyzer = GSCAnalyzer(config)
        cannib_analyzer = CannibalizationAnalyzer(config)
        opp_analyzer = OpportunityAnalyzer(config)
        
        # Run page analysis
        print("  → Analyzing page performance...")
        gsc_issues = gsc_analyzer.analyze_all(page_data)
        
        # Run cannibalization analysis
        print("  → Checking for keyword cannibalization...")
        cannibalization = cannib_analyzer.find_cannibalization(page_query_data)
        
        # Create opportunity report
        print("  → Prioritizing opportunities...")
        opportunities = opp_analyzer.create_opportunity_report(gsc_issues, cannibalization)
        
        print()
        
        # Step 3: Generate summary
        if opportunities.empty:
            print("✅ No major issues found in demo data!")
            return 0
        
        summary = opp_analyzer.get_summary_stats(opportunities)
        
        print("=" * 60)
        print("DEMO ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total Opportunities Found: {summary['total_opportunities']}")
        print(f"  🔴 High Priority:   {summary['high_priority']}")
        print(f"  🟡 Medium Priority: {summary['medium_priority']}")
        print(f"  🟢 Low Priority:    {summary['low_priority']}")
        print()
        print(f"📈 Estimated Monthly Traffic Gain: {int(summary['total_estimated_gain'])} clicks")
        print()
        print(f"Issue Breakdown:")
        print(f"  → Page Optimization: {summary['page_optimization_count']}")
        print(f"  → Cannibalization:   {summary['cannibalization_count']}")
        print("=" * 60)
        print()
        
        # Step 4: Show top opportunities
        quick_wins = opp_analyzer.get_quick_wins(opportunities, limit=5)
        
        if not quick_wins.empty:
            print("TOP 5 QUICK WINS (DEMO DATA)")
            print("-" * 60)
            
            for _, opp in quick_wins.iterrows():
                print(f"\n#{opp['rank']} - {opp['type']} [{opp['priority']} Priority]")
                print(f"   Page: {opp['page']}")
                print(f"   Impact: +{int(opp['estimated_gain'])} clicks/month estimated")
                print(f"   Action: {opp['action']}")
            
            print("\n" + "-" * 60)
            print()
        
        # Step 5: Save reports
        logger.info("Saving demo reports...")
        print("💾 Saving demo reports...")
        
        ensure_output_folder(config['output_folder'])
        output_folder = config['output_folder']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete analysis
        analysis_file = f"{output_folder}/DEMO_analysis_report_{timestamp}.csv"
        gsc_issues.to_csv(analysis_file, index=False)
        print(f"   ✅ {analysis_file}")
        
        # Save opportunities
        opp_file = f"{output_folder}/DEMO_opportunities_{timestamp}.csv"
        opportunities.to_csv(opp_file, index=False)
        print(f"   ✅ {opp_file}")
        
        # Save cannibalization if found
        if not cannibalization.empty:
            cannib_file = f"{output_folder}/DEMO_cannibalization_{timestamp}.csv"
            cannibalization.to_csv(cannib_file, index=False)
            print(f"   ✅ {cannib_file}")
        
        print()
        print("=" * 60)
        print("✅ DEMO ANALYSIS COMPLETE")
        print("=" * 60)
        print()
        print("📊 This is how the system works with REAL data!")
        print()
        print("What you just saw:")
        print("  ✅ Automatic issue detection")
        print("  ✅ Smart prioritization")
        print("  ✅ Traffic gain estimates")
        print("  ✅ Actionable recommendations")
        print()
        print("Next Steps:")
        print("  1. Review the CSV files in reports/ folder")
        print("  2. See how issues are categorized and prioritized")
        print("  3. Understand the analysis logic")
        print()
        print("To use with REAL data:")
        print("  1. Set up Google Search Console access (see README.md)")
        print("  2. Run: python main.py")
        print()
        
        logger.info("Demo analysis completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error in demo mode: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
