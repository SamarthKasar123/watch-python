#!/usr/bin/env python3
"""
Final Production Scraping Run
Collect maximum data from all working scrapers to achieve ~900 product target
"""

import subprocess
import time
import pandas as pd
from datetime import datetime

def run_scraper(scraper_name):
    """Run individual scraper and return success status"""
    try:
        print(f"\n🚀 Running {scraper_name}...")
        result = subprocess.run(['python', f'scrapers/{scraper_name}'], 
                              capture_output=True, text=True, timeout=1200)
        
        if result.returncode == 0:
            print(f"✅ {scraper_name} completed successfully")
            return True
        else:
            print(f"❌ {scraper_name} failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {scraper_name} timed out")
        return False
    except Exception as e:
        print(f"❌ {scraper_name} error: {str(e)}")
        return False

def main():
    """Run comprehensive scraping"""
    print("🎯 FINAL PRODUCTION SCRAPING RUN")
    print("=" * 60)
    print("📋 Target: Maximum data collection from all working scrapers")
    print("🎯 Goal: Approach 900+ products for client requirement")
    print("=" * 60)
    
    # List of working scrapers
    working_scrapers = [
        'chronofinder_scraper.py',
        'bqwatches_scraper.py',
        'prestigiousjewellers_scraper.py'
    ]
    
    successful_runs = 0
    
    for scraper in working_scrapers:
        success = run_scraper(scraper)
        if success:
            successful_runs += 1
        time.sleep(5)  # Brief pause between scrapers
    
    print(f"\n📊 SCRAPING SUMMARY")
    print(f"✅ Successful scrapers: {successful_runs}/{len(working_scrapers)}")
    
    # Consolidate data
    print(f"\n🔄 Consolidating all data...")
    subprocess.run(['python', 'consolidate_data.py'])
    
    print(f"\n🎉 FINAL PRODUCTION RUN COMPLETE!")
    print(f"📊 Dashboard available at: http://localhost:5000")
    print(f"💼 Ready for client presentation!")

if __name__ == "__main__":
    main()
