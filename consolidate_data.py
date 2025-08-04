#!/usr/bin/env python3
"""
Consolidate Data Script
Combines all scraped data files into a single comprehensive dataset
"""

import pandas as pd
import json
from datetime import datetime
import os

def consolidate_data():
    """Consolidate all scraped data into unified files"""
    
    print("🔄 Consolidating scraped data...")
    
    all_data = []
    
    # Load ChronoFinder data
    try:
        cf_df = pd.read_csv('data/chronofinder_watches.csv')
        print(f"✅ ChronoFinder: {len(cf_df)} products")
        all_data.append(cf_df)
    except Exception as e:
        print(f"❌ ChronoFinder: {e}")
    
    # Load BQ Watches data
    try:
        bq_df = pd.read_csv('data/bqwatches_rolex.csv')
        print(f"✅ BQ Watches: {len(bq_df)} products")
        all_data.append(bq_df)
    except Exception as e:
        print(f"❌ BQ Watches: {e}")
    
    if not all_data:
        print("❌ No data files found!")
        return
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True, sort=False)
    
    # Clean and standardize data
    combined_df['price'] = pd.to_numeric(combined_df['price'], errors='coerce')
    combined_df = combined_df.dropna(subset=['price'])
    combined_df = combined_df[combined_df['price'] > 0]
    
    # Standardize brands
    brand_mapping = {
        'ROLEX': 'Rolex',
        'OMEGA': 'Omega', 
        'CARTIER': 'Cartier',
        'AUDEMARS PIGUET': 'Audemars Piguet',
        'PATEK PHILIPPE': 'Patek Philippe',
        'BREITLING': 'Breitling',
        'TAG HEUER': 'Tag Heuer',
        'TUDOR': 'Tudor'
    }
    
    for old_brand, new_brand in brand_mapping.items():
        combined_df.loc[combined_df['brand'].str.upper() == old_brand, 'brand'] = new_brand
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save consolidated files
    csv_file = f'data/consolidated_watches_{timestamp}.csv'
    json_file = f'data/consolidated_watches_{timestamp}.json'
    live_file = 'data/consolidated_watches_live.csv'
    
    combined_df.to_csv(csv_file, index=False)
    combined_df.to_json(json_file, orient='records', indent=2)
    combined_df.to_csv(live_file, index=False)
    
    # Generate summary
    total_products = len(combined_df)
    unique_brands = combined_df['brand'].nunique()
    unique_sites = combined_df['site'].nunique()
    avg_price = combined_df['price'].mean()
    
    print(f"\n📊 CONSOLIDATION COMPLETE!")
    print(f"✅ Total Products: {total_products}")
    print(f"🏷️ Unique Brands: {unique_brands}")
    print(f"🌐 Active Sites: {unique_sites}")
    print(f"💰 Average Price: £{avg_price:,.0f}")
    
    print(f"\n📈 Brand Distribution:")
    brand_counts = combined_df['brand'].value_counts()
    for brand, count in brand_counts.head(8).items():
        if brand and str(brand) != 'nan':
            print(f"  {brand}: {count} products")
    
    print(f"\n📈 Site Distribution:")
    site_counts = combined_df['site'].value_counts()
    for site, count in site_counts.items():
        print(f"  {site}: {count} products")
    
    print(f"\n💾 Files saved:")
    print(f"  📄 {csv_file}")
    print(f"  📄 {json_file}")
    print(f"  📄 {live_file} (for dashboard)")
    
    return total_products

if __name__ == "__main__":
    consolidate_data()
