"""
Simple web dashboard for watch scraping results
"""

from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import json
import os
import glob
from datetime import datetime
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_processor import WatchDataProcessor
from config.settings import config

app = Flask(__name__)

class DashboardData:
    """Manage data for the dashboard"""
    
    def __init__(self):
        self.processor = WatchDataProcessor()
        self.current_data = None
        self.load_latest_data()
    
    def load_latest_data(self):
        """Load the most recent consolidated data file"""
        data_files = glob.glob(os.path.join(config.DATA_DIR, "consolidated_watches_*.csv"))
        
        if data_files:
            latest_file = max(data_files, key=os.path.getctime)
            try:
                self.processor.load_data(latest_file)
                self.current_data = latest_file
                return True
            except Exception as e:
                print(f"Error loading data: {e}")
                return False
        
        return False
    
    def get_summary_stats(self):
        """Get summary statistics for dashboard"""
        if self.processor.df is None:
            return {}
        
        df = self.processor.df
        
        return {
            'total_watches': len(df),
            'total_sites': df['site'].nunique(),
            'total_brands': df['brand'].nunique(),
            'avg_price': df['price'].mean() if 'price' in df.columns else 0,
            'price_range': {
                'min': df['price'].min() if 'price' in df.columns else 0,
                'max': df['price'].max() if 'price' in df.columns else 0
            },
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_brand_distribution(self):
        """Get brand distribution data"""
        if self.processor.df is None:
            return {}
        
        return self.processor.df['brand'].value_counts().head(10).to_dict()
    
    def get_site_distribution(self):
        """Get site distribution data"""
        if self.processor.df is None:
            return {}
        
        return self.processor.df['site'].value_counts().to_dict()
    
    def get_price_distribution(self):
        """Get price distribution by ranges"""
        if self.processor.df is None or 'price' not in self.processor.df.columns:
            return {}
        
        df = self.processor.df
        price_ranges = pd.cut(
            df['price'], 
            bins=[0, 1000, 5000, 10000, 25000, 50000, float('inf')],
            labels=['Under £1K', '£1K-£5K', '£5K-£10K', '£10K-£25K', '£25K-£50K', 'Over £50K']
        )
        
        return price_ranges.value_counts().to_dict()
    
    def search_watches(self, query, limit=50):
        """Search watches by query"""
        if self.processor.df is None:
            return []
        
        df = self.processor.df
        
        # Simple text search across title, brand, model
        mask = (
            df['title'].str.contains(query, case=False, na=False) |
            df['brand'].str.contains(query, case=False, na=False) |
            df['model'].str.contains(query, case=False, na=False)
        )
        
        results = df[mask].head(limit).to_dict('records')
        
        # Clean up results for JSON serialization
        for result in results:
            for key, value in result.items():
                if pd.isna(value):
                    result[key] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    result[key] = value.isoformat()
        
        return results

# Initialize dashboard data
dashboard_data = DashboardData()

@app.route('/')
def index():
    """Main dashboard page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Watch Scraping Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .stats {{ display: flex; justify-content: space-between; margin: 20px 0; }}
            .stat-card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }}
            .stat-card h3 {{ margin: 0; color: #333; }}
            .stat-card p {{ margin: 5px 0; font-size: 24px; font-weight: bold; color: #007cba; }}
            .section {{ margin: 30px 0; }}
            .search-box {{ margin: 20px 0; }}
            .search-box input {{ width: 300px; padding: 10px; font-size: 16px; }}
            .search-box button {{ padding: 10px 20px; font-size: 16px; background: #007cba; color: white; border: none; cursor: pointer; }}
            .watch-list {{ margin: 20px 0; }}
            .watch-item {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .watch-item h4 {{ margin: 0 0 10px 0; }}
            .watch-item .price {{ font-size: 18px; font-weight: bold; color: #28a745; }}
            .watch-item .site {{ color: #6c757d; }}
            .brand-list, .site-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
            .badge {{ background: #007cba; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>Watch Scraping Dashboard</h1>
            
            <div class="stats" id="stats">
                <div class="stat-card">
                    <h3>Total Watches</h3>
                    <p id="total-watches">Loading...</p>
                </div>
                <div class="stat-card">
                    <h3>Sites Scraped</h3>
                    <p id="total-sites">Loading...</p>
                </div>
                <div class="stat-card">
                    <h3>Brands Found</h3>
                    <p id="total-brands">Loading...</p>
                </div>
                <div class="stat-card">
                    <h3>Average Price</h3>
                    <p id="avg-price">Loading...</p>
                </div>
            </div>
            
            <div class="section">
                <h2>Search Watches</h2>
                <div class="search-box">
                    <input type="text" id="search-input" placeholder="Search by brand, model, or title...">
                    <button onclick="searchWatches()">Search</button>
                </div>
                <div id="search-results" class="watch-list"></div>
            </div>
            
            <div class="section">
                <h2>Brand Distribution</h2>
                <div id="brand-distribution" class="brand-list"></div>
            </div>
            
            <div class="section">
                <h2>Site Distribution</h2>
                <div id="site-distribution" class="site-list"></div>
            </div>
            
            <div class="section">
                <h2>Quick Actions</h2>
                <button onclick="refreshData()">Refresh Data</button>
                <button onclick="downloadData()">Download CSV</button>
                <button onclick="runScraping()">Run New Scraping</button>
            </div>
        </div>
        
        <script>
            // Load dashboard data
            function loadDashboard() {{
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('total-watches').textContent = data.total_watches || 0;
                        document.getElementById('total-sites').textContent = data.total_sites || 0;
                        document.getElementById('total-brands').textContent = data.total_brands || 0;
                        document.getElementById('avg-price').textContent = '£' + (data.avg_price || 0).toFixed(0);
                    }});
                
                // Load brand distribution
                fetch('/api/brands')
                    .then(response => response.json())
                    .then(data => {{
                        const container = document.getElementById('brand-distribution');
                        container.innerHTML = '';
                        for (const [brand, count] of Object.entries(data)) {{
                            const badge = document.createElement('span');
                            badge.className = 'badge';
                            badge.textContent = `${{brand}}: ${{count}}`;
                            container.appendChild(badge);
                        }}
                    }});
                
                // Load site distribution
                fetch('/api/sites')
                    .then(response => response.json())
                    .then(data => {{
                        const container = document.getElementById('site-distribution');
                        container.innerHTML = '';
                        for (const [site, count] of Object.entries(data)) {{
                            const badge = document.createElement('span');
                            badge.className = 'badge';
                            badge.textContent = `${{site}}: ${{count}}`;
                            container.appendChild(badge);
                        }}
                    }});
            }}
            
            // Search watches
            function searchWatches() {{
                const query = document.getElementById('search-input').value;
                if (!query) return;
                
                fetch(`/api/search?q=${{encodeURIComponent(query)}}`)
                    .then(response => response.json())
                    .then(data => {{
                        const container = document.getElementById('search-results');
                        container.innerHTML = '';
                        
                        data.forEach(watch => {{
                            const item = document.createElement('div');
                            item.className = 'watch-item';
                            item.innerHTML = `
                                <h4>${{watch.title || 'Unknown Title'}}</h4>
                                <div class="price">£${{watch.price || 'Price not available'}}</div>
                                <div class="site">From: ${{watch.site}}</div>
                                <div>Brand: ${{watch.brand || 'Unknown'}} | Model: ${{watch.model || 'Unknown'}}</div>
                                <div>Reference: ${{watch.reference || 'N/A'}}</div>
                                <a href="${{watch.url}}" target="_blank">View Original</a>
                            `;
                            container.appendChild(item);
                        }});
                    }});
            }}
            
            // Refresh data
            function refreshData() {{
                fetch('/api/refresh', {{method: 'POST'}})
                    .then(() => {{
                        alert('Data refreshed!');
                        loadDashboard();
                    }});
            }}
            
            // Download data
            function downloadData() {{
                window.open('/api/download');
            }}
            
            // Run scraping
            function runScraping() {{
                if (confirm('Start new scraping? This may take a while.')) {{
                    fetch('/api/scrape', {{method: 'POST'}})
                        .then(() => alert('Scraping started! Check console for progress.'));
                }}
            }}
            
            // Load dashboard on page load
            loadDashboard();
        </script>
    </body>
    </html>
    """

@app.route('/api/stats')
def api_stats():
    """Get summary statistics"""
    return jsonify(dashboard_data.get_summary_stats())

@app.route('/api/brands')
def api_brands():
    """Get brand distribution"""
    return jsonify(dashboard_data.get_brand_distribution())

@app.route('/api/sites')
def api_sites():
    """Get site distribution"""
    return jsonify(dashboard_data.get_site_distribution())

@app.route('/api/search')
def api_search():
    """Search watches"""
    query = request.args.get('q', '')
    results = dashboard_data.search_watches(query)
    return jsonify(results)

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Refresh data from latest files"""
    dashboard_data.load_latest_data()
    return jsonify({{'success': True}})

@app.route('/api/download')
def api_download():
    """Download current data as CSV"""
    if dashboard_data.current_data:
        return send_file(dashboard_data.current_data, as_attachment=True)
    else:
        return jsonify({{'error': 'No data available'}})

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Start new scraping (placeholder)"""
    # In a real implementation, this would trigger the scraping process
    return jsonify({{'message': 'Scraping request received. Run main.py to start scraping.'}})

if __name__ == '__main__':
    print("Starting Watch Scraping Dashboard...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
