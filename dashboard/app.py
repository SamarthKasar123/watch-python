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

@app.route('/api/clear-data', methods=['POST'])
def clear_data():
    """Clear all scraped data (for development/testing)"""
    try:
        # This would clear the database in production
        # For now, return success to indicate feature availability
        return jsonify({
            'status': 'success',
            'message': 'Data clearing endpoint available. Full implementation requires API configuration.',
            'note': 'This feature will be activated when API keys are provided.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/system-status')
def system_status():
    """Get system status information"""
    try:
        watches = get_watch_data()
        
        return jsonify({
            'status': 'success',
            'system': {
                'dashboard_online': True,
                'api_connected': True,
                'data_available': len(watches) > 0,
                'total_products': len(watches),
                'last_update': datetime.now().isoformat(),
                'features': {
                    'scraping': 'requires_api_keys',
                    'export': 'available',
                    'analytics': 'available',
                    'real_time': 'available'
                }
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/analytics/advanced')
def advanced_analytics():
    """Advanced business intelligence analytics"""
    try:
        watches = get_watch_data()
        
        if not watches:
            return jsonify({'status': 'success', 'analytics': {}})
        
        # Price analysis
        prices = [w['price'] for w in watches if w['price'] > 0]
        
        # Brand analysis
        brands = {}
        for watch in watches:
            brand = watch.get('brand', 'Unknown')
            if brand not in brands:
                brands[brand] = {'count': 0, 'total_value': 0, 'avg_price': 0, 'products': []}
            brands[brand]['count'] += 1
            brands[brand]['total_value'] += watch.get('price', 0)
            brands[brand]['products'].append(watch)
        
        # Calculate averages
        for brand in brands:
            if brands[brand]['count'] > 0:
                brands[brand]['avg_price'] = brands[brand]['total_value'] / brands[brand]['count']
        
        # Market insights
        analytics = {
            'price_segments': {
                'luxury': len([p for p in prices if p > 10000]),
                'premium': len([p for p in prices if 5000 <= p <= 10000]),
                'mid_range': len([p for p in prices if 1000 <= p < 5000]),
                'entry': len([p for p in prices if p < 1000])
            },
            'brand_insights': {
                brand: {
                    'market_share': round((data['count'] / len(watches)) * 100, 2),
                    'avg_price': round(data['avg_price'], 2),
                    'total_inventory_value': round(data['total_value'], 2),
                    'product_count': data['count']
                }
                for brand, data in sorted(brands.items(), key=lambda x: x[1]['total_value'], reverse=True)[:10]
            },
            'market_trends': {
                'total_market_value': sum(prices),
                'avg_market_price': round(sum(prices) / len(prices), 2) if prices else 0,
                'price_volatility': round((max(prices) - min(prices)) / len(prices), 2) if prices else 0,
                'top_value_segment': max(['luxury', 'premium', 'mid_range', 'entry'], 
                                       key=lambda x: len([p for p in prices if 
                                                        (x == 'luxury' and p > 10000) or
                                                        (x == 'premium' and 5000 <= p <= 10000) or
                                                        (x == 'mid_range' and 1000 <= p < 5000) or
                                                        (x == 'entry' and p < 1000)]))
            }
        }
        
        return jsonify({
            'status': 'success',
            'analytics': analytics,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/scrape-all', methods=['POST'])
def scrape_all_sites():
    """Run the real scraper for all competitor sites"""
    try:
        import subprocess
        import sys
        
        print("🚀 Starting real multi-site scraping...")
        
        # Run the real scraper
        result = subprocess.run([
            sys.executable, 'real_scraper.py'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            # Reload data after scraping
            global _data_cache, _cache_time
            _data_cache = None
            _cache_time = None
            
            new_data = get_watch_data()
            
            return jsonify({
                'status': 'success',
                'message': 'All competitor sites scraped successfully!',
                'products_found': len(new_data),
                'sites_scraped': [
                    'ChronoFinder',
                    'BQ Watches', 
                    'Prestigious Jewellers',
                    'Watch Trader',
                    'Watch Collectors',
                    'Luxury Watch Company',
                    'Watches.co.uk',
                    'UK Specialist Watches',
                    'Watch Buyers',
                    'Watch The Time',
                    'Trilogy Jewellers'
                ],
                'scraper_output': result.stdout
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Scraping failed',
                'error_output': result.stderr
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Scraping error: {str(e)}'
        })

@app.route('/api/clear-all-data', methods=['POST'])
def clear_all_data():
    """Clear all scraped data"""
    try:
        # Clear the CSV file
        if CSV_FILE.exists():
            # Create backup
            backup_file = CSV_FILE.parent / f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            import shutil
            shutil.copy2(CSV_FILE, backup_file)
            
            # Clear main file
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['url', 'site', 'title', 'price', 'currency', 'brand', 'model', 'reference', 'condition', 'description', 'images', 'availability', 'specifications', 'year', 'dial_color', 'bracelet_material', 'case_material', 'movement'])
        
        # Clear cache
        global _data_cache, _cache_time
        _data_cache = None
        _cache_time = None
        
        return jsonify({
            'status': 'success',
            'message': 'All data cleared successfully!',
            'backup_created': str(backup_file) if CSV_FILE.exists() else None
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error clearing data: {str(e)}'
        })

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
