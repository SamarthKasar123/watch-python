#!/usr/bin/env python3
"""
Professional Watch Scraping Dashboard
Modern Flask application with real-time data visualization
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, request
from pathlib import Path
import tempfile
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'watch-scraping-dashboard-2025'

# Data paths
DATA_DIR = project_root / 'data'
CONSOLIDATED_FILE = DATA_DIR / 'consolidated_watches_live.csv'

def load_watch_data():
    """Load watch data from CSV file"""
    try:
        if CONSOLIDATED_FILE.exists():
            df = pd.read_csv(CONSOLIDATED_FILE)
            # Clean and prepare data
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df = df.dropna(subset=['price'])
            return df
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['url', 'site', 'title', 'price', 'currency', 'brand', 'model', 'reference'])
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(columns=['url', 'site', 'title', 'price', 'currency', 'brand', 'model', 'reference'])

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        df = load_watch_data()
        
        if df.empty:
            return jsonify({
                'total_products': 0,
                'active_sites': 0,
                'avg_price': 0,
                'top_brands': 0,
                'min_price': 0,
                'max_price': 0
            })
        
        stats = {
            'total_products': len(df),
            'active_sites': df['site'].nunique(),
            'avg_price': round(df['price'].mean(), 2),
            'top_brands': df['brand'].nunique(),
            'min_price': df['price'].min(),
            'max_price': df['price'].max(),
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products')
def get_products():
    """Get all products with optional filtering"""
    try:
        df = load_watch_data()
        
        # Apply search filter if provided
        search = request.args.get('search', '').lower()
        if search:
            mask = (df['title'].str.lower().str.contains(search, na=False) |
                   df['brand'].str.lower().str.contains(search, na=False) |
                   df['model'].str.lower().str.contains(search, na=False))
            df = df[mask]
        
        # Sort by price descending
        df = df.sort_values('price', ascending=False)
        
        # Convert to dict
        products = df.to_dict('records')
        
        return jsonify(products)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/brands')
def get_brands():
    """Get brand distribution"""
    try:
        df = load_watch_data()
        
        if df.empty:
            return jsonify({})
        
        # Count products by brand
        brand_counts = df['brand'].value_counts().to_dict()
        
        return jsonify(brand_counts)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites')
def get_sites():
    """Get site distribution"""
    try:
        df = load_watch_data()
        
        if df.empty:
            return jsonify({})
        
        # Count products by site
        site_counts = df['site'].value_counts().to_dict()
        
        return jsonify(site_counts)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<format>')
def export_data(format):
    """Export data in various formats"""
    try:
        df = load_watch_data()
        
        if df.empty:
            return jsonify({'error': 'No data to export'}), 400
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'csv':
            filename = f'watch_data_{timestamp}.csv'
            filepath = DATA_DIR / filename
            df.to_csv(filepath, index=False)
            return send_file(filepath, as_attachment=True, download_name=filename)
        
        elif format == 'json':
            filename = f'watch_data_{timestamp}.json'
            filepath = DATA_DIR / filename
            df.to_json(filepath, orient='records', indent=2)
            return send_file(filepath, as_attachment=True, download_name=filename)
        
        elif format == 'excel':
            filename = f'watch_data_{timestamp}.xlsx'
            filepath = DATA_DIR / filename
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # All data
                df.to_excel(writer, sheet_name='All Products', index=False)
                
                # By brand
                for brand in df['brand'].unique():
                    if pd.notna(brand):
                        brand_data = df[df['brand'] == brand]
                        sheet_name = str(brand)[:31]  # Excel sheet name limit
                        brand_data.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Summary sheet
                summary = pd.DataFrame({
                    'Metric': ['Total Products', 'Average Price', 'Min Price', 'Max Price', 'Unique Brands', 'Unique Sites'],
                    'Value': [
                        len(df),
                        f"£{df['price'].mean():.2f}",
                        f"£{df['price'].min():.2f}",
                        f"£{df['price'].max():.2f}",
                        df['brand'].nunique(),
                        df['site'].nunique()
                    ]
                })
                summary.to_excel(writer, sheet_name='Summary', index=False)
            
            return send_file(filepath, as_attachment=True, download_name=filename)
        
        else:
            return jsonify({'error': 'Invalid format'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
def run_scraper():
    """Run the scraper system"""
    try:
        # Run the data collection script
        script_path = project_root / 'collect_real_data.py'
        
        if script_path.exists():
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(project_root)
            )
            
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': 'Scraper completed successfully',
                    'output': result.stdout
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.stderr or 'Scraper failed',
                    'output': result.stdout
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Scraper script not found'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/report')
def generate_report():
    """Generate detailed analysis report"""
    try:
        df = load_watch_data()
        
        if df.empty:
            return "No data available for report generation"
        
        # Generate comprehensive report
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Watch Market Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f0f8ff; padding: 20px; border-radius: 8px; }}
                .section {{ margin: 20px 0; }}
                .stat {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Watch Market Analysis Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="stat">Total Products Analyzed: {len(df)}</div>
                <div class="stat">Average Price: £{df['price'].mean():.2f}</div>
                <div class="stat">Price Range: £{df['price'].min():.2f} - £{df['price'].max():.2f}</div>
                <div class="stat">Market Coverage: {df['site'].nunique()} competitor websites</div>
            </div>
            
            <div class="section">
                <h2>Brand Analysis</h2>
                <table>
                    <tr><th>Brand</th><th>Products</th><th>Avg Price</th><th>Market Share</th></tr>
        """
        
        brand_analysis = df.groupby('brand').agg({
            'price': ['count', 'mean']
        }).round(2)
        
        for brand in brand_analysis.index:
            count = brand_analysis.loc[brand, ('price', 'count')]
            avg_price = brand_analysis.loc[brand, ('price', 'mean')]
            market_share = (count / len(df) * 100)
            
            report_html += f"""
                <tr>
                    <td>{brand}</td>
                    <td>{count}</td>
                    <td>£{avg_price:.2f}</td>
                    <td>{market_share:.1f}%</td>
                </tr>
            """
        
        report_html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Site Performance</h2>
                <table>
                    <tr><th>Site</th><th>Products</th><th>Avg Price</th></tr>
        """
        
        site_analysis = df.groupby('site').agg({
            'price': ['count', 'mean']
        }).round(2)
        
        for site in site_analysis.index:
            count = site_analysis.loc[site, ('price', 'count')]
            avg_price = site_analysis.loc[site, ('price', 'mean')]
            
            report_html += f"""
                <tr>
                    <td>{site}</td>
                    <td>{count}</td>
                    <td>£{avg_price:.2f}</td>
                </tr>
            """
        
        report_html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Pricing Recommendations</h2>
                <p>Based on current market analysis:</p>
                <ul>
                    <li>Consider pricing luxury watches 5-10% below market average for competitive advantage</li>
                    <li>Monitor price fluctuations weekly for optimal positioning</li>
                    <li>Focus on high-demand brands: """ + ", ".join(df['brand'].value_counts().head(3).index.tolist()) + """</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return report_html
    
    except Exception as e:
        return f"Error generating report: {str(e)}"

if __name__ == '__main__':
    print("🚀 Starting Watch Scraping Dashboard...")
    print("📊 Professional UI with real-time data")
    print("🌐 Open http://localhost:5000 in your browser")
    print()
    
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Check if we have data
    if CONSOLIDATED_FILE.exists():
        df = pd.read_csv(CONSOLIDATED_FILE)
        print(f"✅ Loaded {len(df)} products from {df['site'].nunique()} sites")
    else:
        print("⚠️  No data file found - dashboard will show empty state")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
