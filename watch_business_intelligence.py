#!/usr/bin/env python3
"""
Complete Watch Business Intelligence Platform
- Price Comparison with Chrono24 & Google Shopping
- Competitor Scraping & Product Matching
- WooCommerce & Shopify Integration
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import random
from urllib.parse import urljoin, urlparse, quote_plus
import os
from datetime import datetime
import re

class WatchBusinessIntelligence:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        
        # Your store configurations (to be provided)
        self.woocommerce_config = {
            'url': 'YOUR_WOOCOMMERCE_STORE_URL',
            'consumer_key': 'YOUR_CONSUMER_KEY',
            'consumer_secret': 'YOUR_CONSUMER_SECRET'
        }
        
        self.shopify_config = {
            'shop_name': 'YOUR_SHOP_NAME',
            'access_token': 'YOUR_ACCESS_TOKEN'
        }
        
        # Competitor sites
        self.competitor_sites = [
            'https://chronofinder.com/',
            'https://www.prestigiousjewellers.com/',
            'https://www.bqwatches.com/',
            'https://trilogyjewellers.com/',
            'https://www.watchtrader.co.uk/',
            'https://watchcollectors.co.uk/',
            'https://theluxurywatchcompany.com/',
            'https://www.watches.co.uk/',
            'https://www.ukspecialistwatches.co.uk/',
            'https://www.watchbuyers.co.uk/',
            'https://watchthetime.co.uk/'
        ]
        
        self.your_products = []
        self.competitor_products = []
        self.price_comparisons = []
        self.unmatched_products = []
    
    def load_your_products(self):
        """Load your existing 900+ products from WooCommerce + Shopify"""
        print("📦 Loading your store products...")
        
        # WooCommerce products
        woo_products = self.get_woocommerce_products()
        
        # Shopify products  
        shopify_products = self.get_shopify_products()
        
        self.your_products = woo_products + shopify_products
        print(f"✅ Loaded {len(self.your_products)} products from your stores")
        
        return self.your_products
    
    def get_woocommerce_products(self):
        """Fetch all products from WooCommerce store"""
        try:
            # WooCommerce REST API endpoint
            url = f"{self.woocommerce_config['url']}/wp-json/wc/v3/products"
            
            auth = (
                self.woocommerce_config['consumer_key'],
                self.woocommerce_config['consumer_secret']
            )
            
            all_products = []
            page = 1
            per_page = 100
            
            while True:
                params = {
                    'page': page,
                    'per_page': per_page,
                    'status': 'publish'
                }
                
                response = requests.get(url, auth=auth, params=params)
                
                if response.status_code == 200:
                    products = response.json()
                    if not products:
                        break
                        
                    for product in products:
                        product_data = {
                            'id': product['id'],
                            'name': product['name'],
                            'price': float(product['price']) if product['price'] else 0,
                            'sku': product['sku'],
                            'description': product['description'],
                            'brand': self.extract_brand(product['name']),
                            'model': self.extract_model(product['name']),
                            'source': 'woocommerce',
                            'url': product['permalink']
                        }
                        all_products.append(product_data)
                    
                    page += 1
                else:
                    print(f"❌ WooCommerce API error: {response.status_code}")
                    break
            
            return all_products
            
        except Exception as e:
            print(f"❌ WooCommerce error: {e}")
            return []
    
    def get_shopify_products(self):
        """Fetch all products from Shopify store"""
        try:
            url = f"https://{self.shopify_config['shop_name']}.myshopify.com/admin/api/2023-07/products.json"
            
            headers = {
                'X-Shopify-Access-Token': self.shopify_config['access_token']
            }
            
            all_products = []
            page_info = None
            
            while True:
                params = {'limit': 250}
                if page_info:
                    params['page_info'] = page_info
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get('products', [])
                    
                    if not products:
                        break
                    
                    for product in products:
                        for variant in product.get('variants', []):
                            product_data = {
                                'id': variant['id'],
                                'name': product['title'],
                                'price': float(variant['price']) if variant['price'] else 0,
                                'sku': variant['sku'],
                                'description': product['body_html'],
                                'brand': self.extract_brand(product['title']),
                                'model': self.extract_model(product['title']),
                                'source': 'shopify',
                                'url': f"https://{self.shopify_config['shop_name']}.myshopify.com/products/{product['handle']}"
                            }
                            all_products.append(product_data)
                    
                    # Check for pagination
                    link_header = response.headers.get('Link', '')
                    if 'rel="next"' in link_header:
                        # Extract next page info from Link header
                        page_info = self.extract_page_info(link_header)
                    else:
                        break
                else:
                    print(f"❌ Shopify API error: {response.status_code}")
                    break
            
            return all_products
            
        except Exception as e:
            print(f"❌ Shopify error: {e}")
            return []
    
    def compare_prices_chrono24(self, product):
        """Compare product price with Chrono24"""
        try:
            # Build search query
            search_query = f"{product['brand']} {product['model']}".strip()
            search_url = f"https://www.chrono24.com/search/index.htm?query={quote_plus(search_query)}"
            
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find price elements (Chrono24 specific selectors)
                price_elements = soup.find_all(['span', 'div'], class_=re.compile(r'.*price.*', re.I))
                
                prices = []
                for elem in price_elements[:10]:  # Check first 10 results
                    price_text = elem.get_text(strip=True)
                    price = self.extract_price(price_text)
                    if price > 0:
                        prices.append(price)
                
                if prices:
                    min_price = min(prices)
                    avg_price = sum(prices) / len(prices)
                    
                    return {
                        'source': 'chrono24',
                        'min_price': min_price,
                        'avg_price': avg_price,
                        'recommended_price': max(min_price - 100, product['price'] * 0.9),
                        'price_difference': ((product['price'] - min_price) / min_price) * 100 if min_price > 0 else 0,
                        'search_url': search_url
                    }
            
            time.sleep(random.uniform(2, 4))  # Rate limiting
            
        except Exception as e:
            print(f"❌ Chrono24 error for {product['name']}: {e}")
        
        return None
    
    def compare_prices_google_shopping(self, product):
        """Compare product price with Google Shopping"""
        try:
            search_query = f"{product['brand']} {product['model']} watch"
            search_url = f"https://www.google.com/search?tbm=shop&q={quote_plus(search_query)}"
            
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Google Shopping price selectors
                price_elements = soup.find_all(['span', 'div'], text=re.compile(r'[£$€]\d+'))
                
                prices = []
                for elem in price_elements[:10]:
                    price_text = elem.get_text(strip=True)
                    price = self.extract_price(price_text)
                    if price > 0:
                        prices.append(price)
                
                if prices:
                    min_price = min(prices)
                    avg_price = sum(prices) / len(prices)
                    
                    return {
                        'source': 'google_shopping',
                        'min_price': min_price,
                        'avg_price': avg_price,
                        'recommended_price': max(min_price - 100, product['price'] * 0.9),
                        'price_difference': ((product['price'] - min_price) / min_price) * 100 if min_price > 0 else 0,
                        'search_url': search_url
                    }
            
            time.sleep(random.uniform(2, 4))  # Rate limiting
            
        except Exception as e:
            print(f"❌ Google Shopping error for {product['name']}: {e}")
        
        return None
    
    def run_price_comparison(self):
        """Run complete price comparison for all your products"""
        print("💰 Starting price comparison analysis...")
        
        if not self.your_products:
            self.load_your_products()
        
        self.price_comparisons = []
        
        for i, product in enumerate(self.your_products):
            print(f"🔍 Analyzing {i+1}/{len(self.your_products)}: {product['name']}")
            
            comparison = {
                'product': product,
                'chrono24': self.compare_prices_chrono24(product),
                'google_shopping': self.compare_prices_google_shopping(product),
                'timestamp': datetime.now().isoformat()
            }
            
            self.price_comparisons.append(comparison)
            
            # Save progress every 50 products
            if (i + 1) % 50 == 0:
                self.save_price_comparisons()
        
        print(f"✅ Price comparison completed for {len(self.price_comparisons)} products")
        self.save_price_comparisons()
        
        return self.price_comparisons
    
    def scrape_competitor_sites(self):
        """Scrape all competitor sites for product listings"""
        print("🕷️ Starting competitor scraping...")
        
        self.competitor_products = []
        
        scrapers = [
            self.scrape_chronofinder,
            self.scrape_bqwatches,
            self.scrape_prestigiousjewellers,
            self.scrape_watchtrader,
            # Add more scrapers as needed
        ]
        
        for scraper in scrapers:
            try:
                scraper()
                time.sleep(random.uniform(3, 6))
            except Exception as e:
                print(f"❌ Scraper failed: {e}")
                continue
        
        print(f"✅ Competitor scraping completed: {len(self.competitor_products)} products found")
        return self.competitor_products
    
    def match_products(self):
        """Match competitor products with your inventory"""
        print("🔍 Matching competitor products with your inventory...")
        
        if not self.your_products:
            self.load_your_products()
        
        if not self.competitor_products:
            self.scrape_competitor_sites()
        
        matched = []
        unmatched = []
        
        for comp_product in self.competitor_products:
            is_matched = False
            
            for your_product in self.your_products:
                # Matching criteria: brand, model similarity
                if (self.is_similar_product(comp_product, your_product)):
                    matched.append({
                        'competitor_product': comp_product,
                        'your_product': your_product,
                        'match_confidence': self.calculate_match_confidence(comp_product, your_product)
                    })
                    is_matched = True
                    break
            
            if not is_matched:
                unmatched.append(comp_product)
        
        self.unmatched_products = unmatched
        
        print(f"📊 Product matching completed:")
        print(f"   • Matched: {len(matched)} products")
        print(f"   • Unmatched: {len(unmatched)} products")
        
        return matched, unmatched
    
    def add_to_woocommerce(self, product):
        """Add unmatched product to WooCommerce store"""
        try:
            url = f"{self.woocommerce_config['url']}/wp-json/wc/v3/products"
            
            auth = (
                self.woocommerce_config['consumer_key'],
                self.woocommerce_config['consumer_secret']
            )
            
            product_data = {
                'name': product['title'],
                'type': 'simple',
                'regular_price': str(product['price']),
                'description': product.get('description', ''),
                'short_description': f"{product['brand']} {product.get('model', '')}".strip(),
                'categories': [{'name': 'Watches'}],
                'meta_data': [
                    {'key': 'competitor_source', 'value': product['site']},
                    {'key': 'competitor_url', 'value': product['url']},
                    {'key': 'import_date', 'value': datetime.now().isoformat()}
                ]
            }
            
            response = requests.post(url, auth=auth, json=product_data)
            
            if response.status_code == 201:
                return {'status': 'success', 'product_id': response.json()['id']}
            else:
                return {'status': 'error', 'message': response.text}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def add_to_shopify(self, product):
        """Add unmatched product to Shopify store"""
        try:
            url = f"https://{self.shopify_config['shop_name']}.myshopify.com/admin/api/2023-07/products.json"
            
            headers = {
                'X-Shopify-Access-Token': self.shopify_config['access_token'],
                'Content-Type': 'application/json'
            }
            
            product_data = {
                'product': {
                    'title': product['title'],
                    'body_html': product.get('description', ''),
                    'vendor': product['brand'],
                    'product_type': 'Watch',
                    'variants': [{
                        'price': str(product['price']),
                        'inventory_management': 'shopify',
                        'inventory_quantity': 1
                    }],
                    'metafields': [
                        {
                            'namespace': 'competitor',
                            'key': 'source',
                            'value': product['site']
                        },
                        {
                            'namespace': 'competitor',
                            'key': 'original_url',
                            'value': product['url']
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=product_data)
            
            if response.status_code == 201:
                return {'status': 'success', 'product_id': response.json()['product']['id']}
            else:
                return {'status': 'error', 'message': response.text}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    # Scraper methods for each competitor site
    def scrape_chronofinder(self):
        """Scrape ChronoFinder for watch listings"""
        print("🔍 Scraping ChronoFinder...")
        
        urls = [
            'https://chronofinder.com/collections/all',
            'https://chronofinder.com/collections/rolex',
            'https://chronofinder.com/collections/omega'
        ]
        
        for url in urls:
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    products = soup.find_all('div', class_='product-card')
                    
                    for product in products[:20]:
                        product_data = self.extract_product_data(product, 'ChronoFinder', url)
                        if product_data:
                            self.competitor_products.append(product_data)
                            
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"❌ ChronoFinder error: {e}")
    
    def scrape_bqwatches(self):
        """Scrape BQ Watches for listings"""
        print("🔍 Scraping BQ Watches...")
        # Implementation similar to scrape_chronofinder
        pass
    
    def scrape_prestigiousjewellers(self):
        """Scrape Prestigious Jewellers for listings"""  
        print("🔍 Scraping Prestigious Jewellers...")
        # Implementation similar to scrape_chronofinder
        pass
    
    def scrape_watchtrader(self):
        """Scrape Watch Trader for listings"""
        print("🔍 Scraping Watch Trader...")
        # Implementation similar to scrape_chronofinder
        pass
    
    # Utility methods
    def extract_product_data(self, element, site, base_url):
        """Extract product data from HTML element"""
        try:
            title_elem = element.find(['h2', 'h3', 'a'])
            price_elem = element.find(class_=re.compile(r'price', re.I))
            link_elem = element.find('a', href=True)
            
            if title_elem and price_elem:
                return {
                    'title': title_elem.get_text(strip=True),
                    'price': self.extract_price(price_elem.get_text(strip=True)),
                    'currency': 'GBP',
                    'url': urljoin(base_url, link_elem.get('href')) if link_elem else '',
                    'brand': self.extract_brand(title_elem.get_text(strip=True)),
                    'model': self.extract_model(title_elem.get_text(strip=True)),
                    'site': site,
                    'scraped_at': datetime.now().isoformat()
                }
        except Exception as e:
            return None
    
    def extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return 0
        
        price_clean = re.sub(r'[£$€,]', '', price_text)
        price_match = re.search(r'[\d,]+\.?\d*', price_clean)
        
        if price_match:
            try:
                return float(price_match.group().replace(',', ''))
            except:
                return 0
        return 0
    
    def extract_brand(self, title):
        """Extract brand name from title"""
        brands = ['Rolex', 'Omega', 'Patek Philippe', 'Audemars Piguet', 'Cartier', 
                 'Breitling', 'TAG Heuer', 'Hublot', 'Panerai', 'IWC', 'Jaeger-LeCoultre']
        
        title_upper = title.upper()
        for brand in brands:
            if brand.upper() in title_upper:
                return brand
        return 'Unknown'
    
    def extract_model(self, title):
        """Extract model name from title"""
        # Implement model extraction logic
        return ''
    
    def is_similar_product(self, comp_product, your_product):
        """Check if competitor product matches your product"""
        # Implement similarity matching logic
        return False
    
    def calculate_match_confidence(self, comp_product, your_product):
        """Calculate confidence score for product match"""
        return 0.0
    
    def save_price_comparisons(self):
        """Save price comparison results"""
        os.makedirs('data', exist_ok=True)
        
        filename = f'data/price_comparisons_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.price_comparisons, f, indent=2, default=str)
        
        print(f"💾 Price comparisons saved to {filename}")
    
    def generate_business_report(self):
        """Generate comprehensive business intelligence report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'your_products': len(self.your_products),
                'competitor_products': len(self.competitor_products),
                'price_comparisons': len(self.price_comparisons),
                'unmatched_opportunities': len(self.unmatched_products)
            },
            'price_analysis': self.analyze_pricing_opportunities(),
            'competitor_analysis': self.analyze_competitor_landscape(),
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def analyze_pricing_opportunities(self):
        """Analyze pricing opportunities from comparisons"""
        opportunities = []
        
        for comparison in self.price_comparisons:
            if comparison['chrono24'] or comparison['google_shopping']:
                # Calculate opportunity
                pass
        
        return opportunities
    
    def analyze_competitor_landscape(self):
        """Analyze competitor landscape and positioning"""
        return {
            'competitor_count': len(set(p['site'] for p in self.competitor_products)),
            'price_ranges': {},
            'brand_distribution': {}
        }
    
    def generate_recommendations(self):
        """Generate actionable business recommendations"""
        return [
            "Optimize pricing based on competitor analysis",
            "Add high-opportunity unmatched products to inventory",
            "Focus on underrepresented brands in your catalog"
        ]

if __name__ == "__main__":
    # Initialize the business intelligence platform
    wbi = WatchBusinessIntelligence()
    
    print("🚀 Watch Business Intelligence Platform")
    print("=" * 50)
    
    # Example usage:
    # 1. Load your products
    # wbi.load_your_products()
    
    # 2. Run price comparison
    # wbi.run_price_comparison()
    
    # 3. Scrape competitors
    # wbi.scrape_competitor_sites()
    
    # 4. Match products
    # matched, unmatched = wbi.match_products()
    
    # 5. Generate report
    # report = wbi.generate_business_report()
    
    print("✅ Platform ready! Configure your API keys to get started.")
