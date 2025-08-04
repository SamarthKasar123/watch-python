#!/usr/bin/env python3
"""
Real Multi-Site Watch Scraper
Scrapes all competitor websites for watch listings
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import random
from urllib.parse import urljoin, urlparse
import os
from datetime import datetime

class WatchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.sites = {
            'chronofinder': 'https://chronofinder.com/',
            'prestigiousjewellers': 'https://www.prestigiousjewellers.com/',
            'bqwatches': 'https://www.bqwatches.com/',
            'trilogyjewellers': 'https://trilogyjewellers.com/',
            'watchtrader': 'https://www.watchtrader.co.uk/',
            'watchcollectors': 'https://watchcollectors.co.uk/',
            'luxurywatchcompany': 'https://theluxurywatchcompany.com/',
            'watches': 'https://www.watches.co.uk/',
            'ukspecialistwatches': 'https://www.ukspecialistwatches.co.uk/',
            'watchbuyers': 'https://www.watchbuyers.co.uk/',
            'watchthetime': 'https://watchthetime.co.uk/'
        }
        
        self.scraped_products = []
        
    def scrape_chronofinder(self):
        """Scrape ChronoFinder watches"""
        try:
            print("🔍 Scraping ChronoFinder...")
            
            # Multiple category pages
            urls = [
                'https://chronofinder.com/collections/all',
                'https://chronofinder.com/collections/rolex',
                'https://chronofinder.com/collections/omega',
                'https://chronofinder.com/collections/audemars-piguet',
                'https://chronofinder.com/collections/patek-philippe'
            ]
            
            for url in urls:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find product cards
                    products = soup.find_all('div', class_='product-card') or soup.find_all('a', href=True)
                    
                    for product in products[:20]:  # Limit per page
                        try:
                            title = product.find('h3') or product.find('h2') or product.find('.product-title')
                            price = product.find('.price') or product.find('[class*="price"]')
                            link = product.get('href') or product.find('a', href=True)
                            
                            if title and price:
                                product_data = {
                                    'site': 'ChronoFinder',
                                    'title': title.get_text(strip=True),
                                    'price': self.extract_price(price.get_text(strip=True)),
                                    'currency': 'GBP',
                                    'url': urljoin(url, link.get('href') if link else ''),
                                    'brand': self.extract_brand(title.get_text(strip=True)),
                                    'scraped_at': datetime.now().isoformat()
                                }
                                self.scraped_products.append(product_data)
                        except Exception as e:
                            continue
                
                time.sleep(random.uniform(1, 3))  # Random delay
                
        except Exception as e:
            print(f"❌ Error scraping ChronoFinder: {e}")
    
    def scrape_bqwatches(self):
        """Scrape BQ Watches"""
        try:
            print("🔍 Scraping BQ Watches...")
            
            urls = [
                'https://www.bqwatches.com/product-category/buy-a-rolex/daytona/',
                'https://www.bqwatches.com/product-category/buy-a-rolex/',
                'https://www.bqwatches.com/product-category/omega-watches/',
            ]
            
            for url in urls:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    products = soup.find_all('li', class_='product') or soup.find_all('div', class_='product')
                    
                    for product in products[:15]:
                        try:
                            title = product.find('h2') or product.find('h3') or product.find('.woocommerce-loop-product__title')
                            price = product.find('.price') or product.find('.amount')
                            link = product.find('a', href=True)
                            
                            if title and price:
                                product_data = {
                                    'site': 'BQ Watches',
                                    'title': title.get_text(strip=True),
                                    'price': self.extract_price(price.get_text(strip=True)),
                                    'currency': 'GBP',
                                    'url': link.get('href') if link else '',
                                    'brand': self.extract_brand(title.get_text(strip=True)),
                                    'scraped_at': datetime.now().isoformat()
                                }
                                self.scraped_products.append(product_data)
                        except Exception as e:
                            continue
                            
                time.sleep(random.uniform(1, 3))
                
        except Exception as e:
            print(f"❌ Error scraping BQ Watches: {e}")
    
    def scrape_prestigiousjewellers(self):
        """Scrape Prestigious Jewellers"""
        try:
            print("🔍 Scraping Prestigious Jewellers...")
            
            url = 'https://www.prestigiousjewellers.com/product-category/watches/'
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                products = soup.find_all('div', class_='product') or soup.find_all('li', class_='product')
                
                for product in products[:20]:
                    try:
                        title = product.find('h2') or product.find('h3')
                        price = product.find('.price') or product.find('.amount')
                        link = product.find('a', href=True)
                        
                        if title and price:
                            product_data = {
                                'site': 'Prestigious Jewellers',
                                'title': title.get_text(strip=True),
                                'price': self.extract_price(price.get_text(strip=True)),
                                'currency': 'GBP',
                                'url': link.get('href') if link else '',
                                'brand': self.extract_brand(title.get_text(strip=True)),
                                'scraped_at': datetime.now().isoformat()
                            }
                            self.scraped_products.append(product_data)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"❌ Error scraping Prestigious Jewellers: {e}")
    
    def scrape_watchtrader(self):
        """Scrape Watch Trader"""
        try:
            print("🔍 Scraping Watch Trader...")
            
            url = 'https://www.watchtrader.co.uk/shop/'
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                products = soup.find_all('div', class_='product') or soup.find_all('article')
                
                for product in products[:20]:
                    try:
                        title = product.find('h2') or product.find('h3') or product.find('a', {'class': 'woocommerce-LoopProduct-link'})
                        price = product.find('.price') or product.find('.amount')
                        link = product.find('a', href=True)
                        
                        if title and price:
                            product_data = {
                                'site': 'Watch Trader',
                                'title': title.get_text(strip=True),
                                'price': self.extract_price(price.get_text(strip=True)),
                                'currency': 'GBP',
                                'url': link.get('href') if link else '',
                                'brand': self.extract_brand(title.get_text(strip=True)),
                                'scraped_at': datetime.now().isoformat()
                            }
                            self.scraped_products.append(product_data)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"❌ Error scraping Watch Trader: {e}")
    
    def scrape_all_sites(self):
        """Scrape all configured sites"""
        print("🚀 Starting comprehensive watch scraping...")
        
        scrapers = [
            self.scrape_chronofinder,
            self.scrape_bqwatches,
            self.scrape_prestigiousjewellers,
            self.scrape_watchtrader,
        ]
        
        for scraper in scrapers:
            try:
                scraper()
                time.sleep(random.uniform(2, 5))  # Delay between sites
            except Exception as e:
                print(f"❌ Scraper failed: {e}")
                continue
        
        print(f"✅ Scraping completed! Found {len(self.scraped_products)} products")
        return self.scraped_products
    
    def extract_price(self, price_text):
        """Extract numeric price from text"""
        import re
        if not price_text:
            return 0
        
        # Remove currency symbols and extract numbers
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
                 'Breitling', 'TAG Heuer', 'Hublot', 'Panerai', 'IWC', 'Jaeger-LeCoultre',
                 'Vacheron Constantin', 'Chopard', 'Tudor', 'Longines', 'Tissot']
        
        title_upper = title.upper()
        for brand in brands:
            if brand.upper() in title_upper:
                return brand
        return 'Unknown'
    
    def save_to_csv(self, filename='data/consolidated_watches_live.csv'):
        """Save scraped data to CSV"""
        if not self.scraped_products:
            return
        
        os.makedirs('data', exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['site', 'title', 'price', 'currency', 'brand', 'url', 'scraped_at']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.scraped_products)
        
        print(f"💾 Data saved to {filename}")

if __name__ == "__main__":
    scraper = WatchScraper()
    products = scraper.scrape_all_sites()
    scraper.save_to_csv()
    print(f"🎉 Scraping complete! {len(products)} products found")
