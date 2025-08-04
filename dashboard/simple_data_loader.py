#!/usr/bin/env python3
"""
Simple CSV reader for dashboard without pandas dependency
"""

import csv
import json
from pathlib import Path

def load_watch_data_simple():
    """Load watch data from CSV file using pure Python"""
    try:
        data_dir = Path(__file__).parent.parent / 'data'
        csv_file = data_dir / 'consolidated_watches_live.csv'
        
        if not csv_file.exists():
            return []
        
        watches = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean and convert price
                try:
                    price_str = row.get('price', '0').replace(',', '').replace('£', '').replace('$', '')
                    price = float(price_str) if price_str else 0
                except:
                    price = 0
                
                watch = {
                    'title': row.get('title', ''),
                    'price': price,
                    'currency': row.get('currency', 'GBP'),
                    'brand': row.get('brand', ''),
                    'site': row.get('site', ''),
                    'url': row.get('url', ''),
                    'model': row.get('model', ''),
                    'condition': row.get('condition', ''),
                    'year': row.get('year', ''),
                    'description': row.get('description', '')
                }
                watches.append(watch)
        
        return watches
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

def get_stats_simple(watches):
    """Calculate simple statistics without pandas"""
    if not watches:
        return {
            'total_watches': 0,
            'total_sites': 0,
            'total_brands': 0,
            'avg_price': 0,
            'price_range': [0, 0]
        }
    
    # Basic stats
    total_watches = len(watches)
    sites = set(w['site'] for w in watches if w['site'])
    brands = set(w['brand'] for w in watches if w['brand'])
    prices = [w['price'] for w in watches if w['price'] > 0]
    
    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    
    return {
        'total_watches': total_watches,
        'total_sites': len(sites),
        'total_brands': len(brands),
        'avg_price': round(avg_price, 2),
        'price_range': [min_price, max_price]
    }

def get_brand_distribution(watches):
    """Get brand distribution for charts"""
    brand_counts = {}
    for watch in watches:
        brand = watch.get('brand', 'Unknown')
        if brand:
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
    
    # Sort by count and take top 10
    sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'labels': [brand for brand, count in sorted_brands],
        'data': [count for brand, count in sorted_brands]
    }

def get_site_distribution(watches):
    """Get site distribution for charts"""
    site_counts = {}
    for watch in watches:
        site = watch.get('site', 'Unknown')
        if site:
            site_counts[site] = site_counts.get(site, 0) + 1
    
    sorted_sites = sorted(site_counts.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'labels': [site for site, count in sorted_sites],
        'data': [count for site, count in sorted_sites]
    }

def search_watches(watches, query):
    """Search watches by title, brand, or model"""
    if not query:
        return watches
    
    query = query.lower()
    results = []
    
    for watch in watches:
        searchable_text = f"{watch.get('title', '')} {watch.get('brand', '')} {watch.get('model', '')}".lower()
        if query in searchable_text:
            results.append(watch)
    
    return results
