#!/usr/bin/env python3
"""
Comprehensive Watch Scraper - Final Production Run
Scrapes all 11 competitor websites to gather ~900 products for client
"""

import os
import sys
import time
import pandas as pd
from pathlib import Path
import importlib.util

def load_scraper_module(scraper_path):
    """Dynamically load a scraper module"""
    spec = importlib.util.spec_from_file_location("scraper", scraper_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_comprehensive_scraping():
    """Run all scrapers to gather comprehensive data"""
    
    print("🚀 STARTING COMPREHENSIVE WATCH SCRAPING")
    print("=" * 60)
    print("📋 Target: ~900 products from 11 competitor websites")
    print("🎯 Client Requirements: Complete product data collection")
    print("=" * 60)
    
    # Define all scrapers
    scrapers = [
        ("ChronoFinder", "scrapers/chronofinder_scraper.py"),
        ("Prestigious Jewellers", "scrapers/prestigious_jewellers_scraper.py"),
        ("BQ Watches", "scrapers/bq_watches_scraper.py"),
        ("Trilogy Jewellers", "scrapers/trilogy_jewellers_scraper.py"),
        ("Watch Trader", "scrapers/watchtrader_scraper.py"),
        ("Watch Collectors", "scrapers/watchcollectors_scraper.py"),
        ("Luxury Watch Company", "scrapers/luxury_watch_company_scraper.py"),
        ("Watches.co.uk", "scrapers/watches_uk_scraper.py"),
        ("UK Specialist Watches", "scrapers/uk_specialist_watches_scraper.py"),
        ("Watch Buyers", "scrapers/watchbuyers_scraper.py"),
        ("Watch The Time", "scrapers/watchthetime_scraper.py")
    ]
    
    total_products = 0
    successful_scrapers = 0
    failed_scrapers = []
    
    for site_name, scraper_path in scrapers:
        print(f"\n🔄 Scraping {site_name}...")
        print(f"📂 File: {scraper_path}")
        
        try:
            if os.path.exists(scraper_path):
                # Run the scraper
                os.system(f"python {scraper_path}")
                
                # Check if data was generated
                csv_name = scraper_path.replace("scrapers/", "data/").replace("_scraper.py", "_watches.csv")
                if os.path.exists(csv_name):
                    df = pd.read_csv(csv_name)
                    products_count = len(df)
                    total_products += products_count
                    successful_scrapers += 1
                    print(f"✅ {site_name}: {products_count} products scraped")
                else:
                    print(f"⚠️ {site_name}: No data file generated")
                    failed_scrapers.append(site_name)
            else:
                print(f"❌ {site_name}: Scraper file not found")
                failed_scrapers.append(site_name)
                
        except Exception as e:
            print(f"❌ {site_name}: Error - {str(e)}")
            failed_scrapers.append(site_name)
        
        # Brief pause between scrapers
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("📊 SCRAPING SUMMARY")
    print("=" * 60)
    print(f"✅ Successful scrapers: {successful_scrapers}/11")
    print(f"📦 Total products collected: {total_products}")
    print(f"🎯 Target achievement: {(total_products/900)*100:.1f}% of 900 products")
    
    if failed_scrapers:
        print(f"❌ Failed scrapers: {', '.join(failed_scrapers)}")
    
    # Consolidate all data
    print(f"\n🔄 Consolidating data from all sources...")
    os.system("python consolidate_data.py")
    
    # Check final consolidated file
    consolidated_file = "data/consolidated_watches_live.csv"
    if os.path.exists(consolidated_file):
        final_df = pd.read_csv(consolidated_file)
        final_count = len(final_df)
        print(f"✅ Consolidated dataset: {final_count} total products")
        
        # Show breakdown by site
        print("\n📊 BREAKDOWN BY WEBSITE:")
        site_counts = final_df['site'].value_counts()
        for site, count in site_counts.items():
            print(f"   📍 {site}: {count} products")
    
    print("\n🎉 COMPREHENSIVE SCRAPING COMPLETED!")
    print("💼 Ready for client delivery")
    
    return total_products >= 800  # Allow some flexibility from 900 target

if __name__ == "__main__":
    success = run_comprehensive_scraping()
    if success:
        print("\n✅ PROJECT SUCCESSFULLY COMPLETED")
        print("🚀 Dashboard ready at: http://localhost:5000")
    else:
        print("\n⚠️ Target not fully achieved - debugging required")
