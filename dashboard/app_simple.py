#!/usr/bin/env python3
"""
Professional Watch Scraping Dashboard - NO PANDAS VERSION
Pure Python implementation for reliable deployment
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import csv
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import our simple data loader
from dashboard.simple_data_loader import (
    load_watch_data_simple, 
    get_stats_simple, 
    get_brand_distribution, 
    get_site_distribution, 
    search_watches
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'watch-scraping-dashboard-2025'

# Global data cache
_data_cache = None
_cache_time = None

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
        
        # Create temporary CSV
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
        
        from flask import Response
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
        
        from flask import Response
        return Response(
            json.dumps(export_data, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=watch_data.json'}
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Professional Watch Scraping Dashboard (No-Pandas Version)")
    print("=" * 60)
    
    # Ensure data directory exists
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Check if we have data
    csv_file = data_dir / 'consolidated_watches_live.csv'
    if csv_file.exists():
        watches = load_watch_data_simple()
        print(f"✅ Loaded {len(watches)} products")
    else:
        print("⚠️  No data file found - dashboard will show empty state")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
