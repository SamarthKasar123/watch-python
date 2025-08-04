import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

class ChronoFinderScraper(BaseScraper):
    """Scraper for ChronoFinder.com"""
    
    def __init__(self):
        super().__init__(
            base_url="https://chronofinder.com",
            site_name="chronofinder",
            use_selenium=True
        )
        
        # URL patterns for different watch categories
        self.category_urls = [
            "https://chronofinder.com/collections/all",
            "https://chronofinder.com/collections/audemars-piguet",
            "https://chronofinder.com/collections/patek-philippe",
            "https://chronofinder.com/collections/pre-owned-omega",
            "https://chronofinder.com/collections/pre-owned-breitling",
            "https://chronofinder.com/pages/shop-by-model-rolex-new"
        ]
    
    def scrape_product_links(self, category_url: str) -> list:
        """Extract all product links from a category page"""
        self.logger.info(f"Scraping product links from: {category_url}")
        
        soup = self.get_page(category_url)
        if not soup:
            return []
        
        product_links = []
        
        # Look for product links (updated selectors for ChronoFinder)
        link_selectors = [
            'a[href*="/products/"]',
            '.product-item a',
            '.product-card a', 
            '.grid-product__link',
            '.product-link',
            'a[href*="/collections/all/products/"]'
        ]
        
        for selector in link_selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href and '/products/' in href:
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        if full_url not in product_links:
                            product_links.append(full_url)
                break
        
        # Handle pagination
        pagination_links = soup.select('a[href*="page="], .pagination a, .next')
        for page_link in pagination_links[:5]:  # Limit to first 5 pages for now
            href = page_link.get('href')
            if href and 'page=' in href:
                page_url = href if href.startswith('http') else f"{self.base_url}{href}"
                self.random_delay()
                page_soup = self.get_page(page_url)
                if page_soup:
                    for selector in link_selectors:
                        page_links = page_soup.select(selector)
                        if page_links:
                            for link in page_links:
                                href = link.get('href')
                                if href and '/products/' in href:
                                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                                    if full_url not in product_links:
                                        product_links.append(full_url)
                            break
        
        self.logger.info(f"Found {len(product_links)} product links")
        return product_links
    
    def scrape_product_details(self, product_url: str) -> dict:
        """Scrape detailed information from a product page"""
        self.logger.info(f"Scraping product: {product_url}")
        
        soup = self.get_page(product_url)
        if not soup:
            return {}
        
        product_data = {
            'url': product_url,
            'site': self.site_name,
            'title': '',
            'price': None,
            'currency': 'GBP',
            'brand': '',
            'model': '',
            'reference': '',
            'condition': '',
            'description': '',
            'images': [],
            'availability': '',
            'specifications': {}
        }
        
        try:
            # Extract title
            title_selectors = [
                '.product-single__title',
                '.product__title',
                'h1.product-title',
                'h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    product_data['title'] = self.clean_text(title_elem.get_text())
                    break
            
            # Extract price
            price_selectors = [
                '.price',
                '.product-single__price',
                '.product__price',
                '.money',
                '[data-price]'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text()
                    product_data['price'] = self.extract_price(price_text)
                    if product_data['price']:
                        break
            
            # Extract description
            desc_selectors = [
                '.product-single__description',
                '.product__description',
                '.product-description',
                '.rte'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product_data['description'] = self.clean_text(desc_elem.get_text())
                    break
            
            # Extract images
            img_selectors = [
                '.product-single__photo img',
                '.product__photo img',
                '.product-images img'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                if images:
                    for img in images:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            img_url = src if src.startswith('http') else f"{self.base_url}{src}"
                            if img_url not in product_data['images']:
                                product_data['images'].append(img_url)
                    break
            
            # Extract watch details
            watch_details = self.extract_watch_details(
                product_data['title'], 
                product_data['description']
            )
            product_data.update(watch_details)
            
            # Extract specifications from structured data
            specs_selectors = [
                '.product-single__meta',
                '.product__meta',
                '.product-specifications'
            ]
            
            for selector in specs_selectors:
                specs_elem = soup.select_one(selector)
                if specs_elem:
                    specs_text = specs_elem.get_text()
                    # Parse specifications (brand specific logic can be added here)
                    if 'reference' in specs_text.lower():
                        ref_match = re.search(r'reference[:\s]*(\w+)', specs_text.lower())
                        if ref_match:
                            product_data['reference'] = ref_match.group(1).upper()
                    break
            
            # Check availability
            availability_indicators = [
                '.product-form__availability',
                '.stock-status',
                '.availability'
            ]
            
            for selector in availability_indicators:
                avail_elem = soup.select_one(selector)
                if avail_elem:
                    product_data['availability'] = self.clean_text(avail_elem.get_text())
                    break
            
            # Default availability based on price presence
            if not product_data['availability']:
                product_data['availability'] = 'In Stock' if product_data['price'] else 'Contact for Price'
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {str(e)}")
        
        return product_data
    
    def scrape(self) -> list:
        """Main scraping method"""
        self.logger.info("Starting ChronoFinder scraping...")
        
        all_product_links = []
        
        # Collect all product links from category pages
        for category_url in self.category_urls:
            try:
                links = self.scrape_product_links(category_url)
                all_product_links.extend(links)
                self.random_delay(2, 4)  # Longer delay between categories
            except Exception as e:
                self.logger.error(f"Error scraping category {category_url}: {str(e)}")
        
        # Remove duplicates
        all_product_links = list(set(all_product_links))
        self.logger.info(f"Found total {len(all_product_links)} unique products")
        
        # Scrape each product (limit for testing)
        max_products = 100  # Adjust as needed
        for i, product_url in enumerate(all_product_links[:max_products]):
            try:
                product_data = self.scrape_product_details(product_url)
                if product_data and product_data.get('title'):
                    self.scraped_data.append(product_data)
                    self.logger.info(f"Scraped product {i+1}/{min(len(all_product_links), max_products)}: {product_data['title']}")
                
                self.random_delay()
                
            except Exception as e:
                self.logger.error(f"Error scraping product {product_url}: {str(e)}")
        
        self.logger.info(f"Completed scraping. Total products: {len(self.scraped_data)}")
        return self.scraped_data

if __name__ == "__main__":
    with ChronoFinderScraper() as scraper:
        data = scraper.scrape()
        scraper.save_data("chronofinder_watches")
        print(f"Scraped {len(data)} products from ChronoFinder")
