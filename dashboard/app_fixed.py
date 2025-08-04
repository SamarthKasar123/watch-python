#!/usr/bin/env python3
"""
Professional Watch Scraping Dashboard - SELF-CONTAINED VERSION
Pure Python implementation with embedded data loading
"""

import os
import sys
import json
import csv
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'watch-scraping-dashboard-2025'

# Data paths
project_root = Path(__file__).parent.parent
DATA_DIR = project_root / 'data'
CSV_FILE = DATA_DIR / 'consolidated_watches_live.csv'

# Global data cache
_data_cache = None
_cache_time = None

def load_watch_data_simple():
    """Load watch data from CSV file using pure Python"""
    try:
        if not CSV_FILE.exists():
            return []
        
        watches = []
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
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

def get_watch_data():
    """Get watch data with simple caching"""
    global _data_cache, _cache_time
    
    # Cache for 5 minutes
    if _data_cache is None or _cache_time is None or (datetime.now() - _cache_time).seconds > 300:
        _data_cache = load_watch_data_simple()
        _cache_time = datetime.now()
    
    return _data_cache

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        watches = get_watch_data()
        stats = get_stats_simple(watches)
        
        return render_template('index.html', 
                             total_watches=stats['total_watches'],
                             total_sites=stats['total_sites'],
                             total_brands=stats['total_brands'])
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('index.html', 
                             total_watches=0,
                             total_sites=0,
                             total_brands=0)

@app.route('/api/data')
def api_data():
    """API endpoint for watch data"""
    try:
        watches = get_watch_data()
        query = request.args.get('search', '')
        
        if query:
            watches = search_watches(watches, query)
        
        # Limit to first 100 for performance
        limited_watches = watches[:100]
        
        return jsonify({
            'status': 'success',
            'data': limited_watches,
            'total': len(watches),
            'displayed': len(limited_watches)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    try:
        watches = get_watch_data()
        stats = get_stats_simple(watches)
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/charts/brands')
def api_chart_brands():
    """API endpoint for brand distribution chart"""
    try:
        watches = get_watch_data()
        distribution = get_brand_distribution(watches)
        
        return jsonify({
            'status': 'success',
            'chart_data': distribution
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/charts/sites')
def api_chart_sites():
    """API endpoint for site distribution chart"""
    try:
        watches = get_watch_data()
        distribution = get_site_distribution(watches)
        
        return jsonify({
            'status': 'success',
            'chart_data': distribution
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/export/csv')
def export_csv():
    """Export data as CSV"""
    try:
        watches = get_watch_data()
        
        # Create CSV content
        output = []
        output.append('title,price,currency,brand,site,url,model,condition,year')
        
        for watch in watches:
            row = [
                str(watch.get('title', '')).replace(',', ';'),
                str(watch.get('price', 0)),
                str(watch.get('currency', 'GBP')),
                str(watch.get('brand', '')).replace(',', ';'),
                str(watch.get('site', '')).replace(',', ';'),
                str(watch.get('url', '')),
                str(watch.get('model', '')).replace(',', ';'),
                str(watch.get('condition', '')).replace(',', ';'),
                str(watch.get('year', ''))
            ]
            output.append(','.join(row))
        
        csv_content = '\n'.join(output)
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=watch_data.csv'}
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/export/json')
def export_json():
    """Export data as JSON"""
    try:
        watches = get_watch_data()
        stats = get_stats_simple(watches)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'statistics': stats,
            'watches': watches
        }
        
        return Response(
            json.dumps(export_data, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=watch_data.json'}
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Professional Watch Scraping Dashboard (Self-Contained Version)")
    print("=" * 70)
    
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Check if we have data
    if CSV_FILE.exists():
        watches = load_watch_data_simple()
        print(f"✅ Loaded {len(watches)} products")
    else:
        print("⚠️  No data file found - dashboard will show empty state")
        print(f"📁 Looking for: {CSV_FILE}")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Dashboard starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
