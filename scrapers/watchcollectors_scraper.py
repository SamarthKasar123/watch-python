#!/usr/bin/env python3
"""
Watch Collectors UK Scraper
Scrapes watch listings from watchcollectors.co.uk
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import csv
import json
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_scraper import BaseScraper

class WatchCollectorsScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.site_name = "watchcollectors"
        self.base_url = "https://watchcollectors.co.uk"
        self.start_urls = [
            "https://watchcollectors.co.uk/collections/all",
            "https://watchcollectors.co.uk/collections/rolex",
            "https://watchcollectors.co.uk/collections/omega",
            "https://watchcollectors.co.uk/collections/cartier"
        ]

    def extract_watch_info(self, soup, url):
        """Extract watch information from product page"""
        watch_data = {
            'url': url,
            'site': self.site_name,
            'title': '',
            'price': 0,
            'currency': 'GBP',
            'brand': '',
            'model': '',
            'reference': '',
            'condition': '',
            'year': '',
            'case_material': '',
            'dial_color': '',
            'bracelet_material': '',
            'movement': '',
            'description': '',
            'images': [],
            'availability': '',
            'specifications': {}
        }

        try:
            # Extract title
            title_elem = soup.find('h1', class_='product-single__title') or soup.find('h1')
            if title_elem:
                watch_data['title'] = title_elem.get_text(strip=True)

            # Extract price
            price_elem = soup.find('span', class_='product-single__price') or soup.find('span', class_='money')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'£([\d,]+)', price_text)
                if price_match:
                    watch_data['price'] = float(price_match.group(1).replace(',', ''))

            # Extract brand from title or URL
            title = watch_data['title'].upper()
            url_upper = url.upper()
            brands = ['ROLEX', 'OMEGA', 'CARTIER', 'PATEK PHILIPPE', 'AUDEMARS PIGUET', 'BREITLING', 'TAG HEUER', 'TUDOR']
            for brand in brands:
                if brand in title or brand in url_upper:
                    watch_data['brand'] = brand.title()
                    break

            # Extract description
            desc_elem = soup.find('div', class_='product-single__description') or soup.find('div', class_='rte')
            if desc_elem:
                watch_data['description'] = desc_elem.get_text(strip=True)

            # Extract images
            img_elements = soup.find_all('img', src=True)
            for img in img_elements:
                src = img.get('src')
                if src and ('product' in src.lower() or 'files' in src.lower()):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.base_url + src
                    watch_data['images'].append(src)

            # Extract availability from Shopify
            form_elem = soup.find('form', class_='product-form')
            if form_elem:
                button = form_elem.find('button', type='submit')
                if button:
                    button_text = button.get_text(strip=True)
                    if 'sold out' in button_text.lower():
                        watch_data['availability'] = 'Sold Out'
                    else:
                        watch_data['availability'] = 'In Stock'

        except Exception as e:
            self.logger.error(f"Error extracting watch info from {url}: {str(e)}")

        return watch_data

    def scrape_product_urls(self, category_url, max_products=30):
        """Scrape product URLs from category page"""
        urls = []
        try:
            response = self.session.get(category_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find product links (Shopify structure)
            product_links = soup.find_all('a', href=True)
            for link in product_links:
                href = link.get('href')
                if href and '/products/' in href:
                    if href.startswith('/'):
                        href = self.base_url + href
                    if href not in urls:
                        urls.append(href)
                        if len(urls) >= max_products:
                            break

            self.logger.info(f"Found {len(urls)} product URLs from {category_url}")

        except Exception as e:
            self.logger.error(f"Error scraping category {category_url}: {str(e)}")

        return urls

    def scrape_site(self, max_products_per_page=25):
        """Scrape all watches from the site"""
        self.logger.info(f"🚀 Starting {self.site_name} scraper...")
        
        all_urls = []
        for start_url in self.start_urls:
            urls = self.scrape_product_urls(start_url, max_products_per_page)
            all_urls.extend(urls)
            time.sleep(2)  # Rate limiting

        # Remove duplicates
        all_urls = list(set(all_urls))
        self.logger.info(f"📦 Found {len(all_urls)} unique product URLs")

        watches = []
        for i, url in enumerate(all_urls, 1):
            try:
                self.logger.info(f"Scraping {i}/{len(all_urls)}: {url}")
                
                response = self.session.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                watch_data = self.extract_watch_info(soup, url)
                if watch_data['title'] and watch_data['price'] > 0:
                    watches.append(watch_data)
                    self.logger.info(f"✅ Extracted: {watch_data['title']} - £{watch_data['price']:,.0f}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"❌ Error scraping {url}: {str(e)}")
                continue

        self.logger.info(f"🎉 Completed! Scraped {len(watches)} watches from {self.site_name}")
        return watches

def main():
    scraper = WatchCollectorsScraper()
    watches = scraper.scrape_site(max_products_per_page=20)
    
    if watches:
        filename = scraper.save_to_csv(watches)
        scraper.save_to_json(watches, filename.replace('.csv', '.json'))
        print(f"\n✅ Saved {len(watches)} watches to {filename}")
    else:
        print("❌ No watches were scraped")

if __name__ == "__main__":
    main()
