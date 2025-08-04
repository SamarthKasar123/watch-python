import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_scraper import BaseScraper
import re

class BQWatchesScraper(BaseScraper):
    """Scraper for BQWatches.com - Rolex Specialist"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.bqwatches.com",
            site_name="bqwatches",
            use_selenium=False
        )
        
        self.category_urls = [
            "https://www.bqwatches.com/product-category/buy-a-rolex/daytona/",
            "https://www.bqwatches.com/product-category/buy-a-rolex/submariner/",
            "https://www.bqwatches.com/product-category/buy-a-rolex/gmt-master/",
            "https://www.bqwatches.com/product-category/buy-a-rolex/datejust/",
            "https://www.bqwatches.com/product-category/buy-a-rolex/explorer/",
            "https://www.bqwatches.com/product-category/buy-a-rolex/sea-dweller/",
            "https://www.bqwatches.com/product-category/buy-a-rolex/yacht-master/",
            "https://www.bqwatches.com/product-category/buy-a-rolex/"
        ]
    
    def scrape_product_links(self, category_url: str) -> list:
        """Extract product links from category page"""
        self.logger.info(f"Scraping product links from: {category_url}")
        
        soup = self.get_page(category_url)
        if not soup:
            return []
        
        product_links = []
        
        # WooCommerce selectors
        link_selectors = [
            '.woocommerce-loop-product__link',
            '.product .entry-title a',
            'a[href*="/product/"]',
            '.products .product a'
        ]
        
        for selector in link_selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href and '/product/' in href:
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        if full_url not in product_links:
                            product_links.append(full_url)
                break
        
        # Handle pagination
        next_page = soup.select_one('.next.page-numbers')
        if next_page:
            next_url = next_page.get('href')
            if next_url:
                self.random_delay()
                additional_links = self.scrape_product_links(next_url)
                product_links.extend(additional_links)
        
        self.logger.info(f"Found {len(product_links)} product links")
        return product_links
    
    def scrape_product_details(self, product_url: str) -> dict:
        """Scrape Rolex product details"""
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
            'brand': 'Rolex',  # BQ Watches specializes in Rolex
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
            title_elem = soup.select_one('h1.py-2, .product_title, h1.entry-title')
            if title_elem:
                product_data['title'] = self.clean_text(title_elem.get_text())
            
            # Extract price  
            price_selectors = [
                'p.highlight.fs-4.fw-bold',  # Updated selector for BQ Watches
                '.price .woocommerce-Price-amount',
                '.price ins .amount',
                '.summary .price .amount'
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
                '.woocommerce-product-details__short-description',
                '.product-description',
                '#tab-description'
            ]
            
            description_parts = []
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    desc_text = self.clean_text(desc_elem.get_text())
                    if desc_text:
                        description_parts.append(desc_text)
            
            product_data['description'] = ' '.join(description_parts)
            
            # Extract images
            images = soup.select('.woocommerce-product-gallery__image img, .product-images img')
            for img in images:
                src = img.get('src') or img.get('data-src')
                if src:
                    img_url = src if src.startswith('http') else f"{self.base_url}{src}"
                    if img_url not in product_data['images']:
                        product_data['images'].append(img_url)
            
            # Extract Rolex-specific details
            watch_details = self.extract_rolex_details(
                product_data['title'], 
                product_data['description']
            )
            product_data.update(watch_details)
            
            # Extract specifications from product attributes
            attributes = soup.select('.woocommerce-product-attributes tr')
            for attr in attributes:
                label_elem = attr.select_one('.woocommerce-product-attributes-item__label')
                value_elem = attr.select_one('.woocommerce-product-attributes-item__value')
                
                if label_elem and value_elem:
                    label = self.clean_text(label_elem.get_text()).replace(':', '').lower()
                    value = self.clean_text(value_elem.get_text())
                    product_data['specifications'][label] = value
                    
                    # Map to standard fields
                    if 'reference' in label or 'model' in label:
                        product_data['reference'] = value
                    elif 'condition' in label:
                        product_data['condition'] = value
            
            # Check availability
            stock_elem = soup.select_one('.stock')
            if stock_elem:
                product_data['availability'] = self.clean_text(stock_elem.get_text())
            else:
                product_data['availability'] = 'Contact for Availability'
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {str(e)}")
        
        return product_data
    
    def extract_rolex_details(self, title: str, description: str) -> dict:
        """Extract Rolex-specific details"""
        details = {
            'brand': 'Rolex',
            'model': '',
            'reference': '',
            'year': '',
            'condition': '',
            'dial_color': '',
            'bracelet_material': '',
            'case_material': '',
            'movement': 'Automatic'
        }
        
        text = f"{title} {description}".lower()
        
        # Rolex models
        rolex_models = [
            'submariner', 'daytona', 'gmt-master', 'datejust', 'day-date',
            'explorer', 'sea-dweller', 'yacht-master', 'milgauss', 'air-king',
            'cellini', 'oyster perpetual', 'cosmograph'
        ]
        
        for model in rolex_models:
            if model in text:
                details['model'] = model.title()
                break
        
        # Reference patterns for Rolex
        ref_patterns = [
            r'\b(1\d{4,5}[a-zA-Z]*)\b',  # Rolex 5-6 digit refs
            r'\b(2\d{4,5}[a-zA-Z]*)\b',
            r'ref[:\.\s]*(\d{5,6}[a-zA-Z]*)',
            r'reference[:\.\s]*(\d{5,6}[a-zA-Z]*)'
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text)
            if match:
                details['reference'] = match.group(1).upper()
                break
        
        # Dial colors
        dial_colors = ['black', 'white', 'blue', 'green', 'silver', 'champagne', 'gold']
        for color in dial_colors:
            if f"{color} dial" in text:
                details['dial_color'] = color.title()
                break
        
        # Bracelet/strap materials
        if 'oyster' in text:
            details['bracelet_material'] = 'Oyster Bracelet'
        elif 'jubilee' in text:
            details['bracelet_material'] = 'Jubilee Bracelet'
        elif 'leather' in text:
            details['bracelet_material'] = 'Leather Strap'
        
        # Case materials
        if 'steel' in text:
            details['case_material'] = 'Stainless Steel'
        elif 'gold' in text:
            details['case_material'] = 'Gold'
        elif 'platinum' in text:
            details['case_material'] = 'Platinum'
        
        return details
    
    def scrape(self) -> list:
        """Main scraping method"""
        self.logger.info("Starting BQ Watches scraping...")
        
        all_product_links = []
        
        for category_url in self.category_urls:
            try:
                links = self.scrape_product_links(category_url)
                all_product_links.extend(links)
                self.random_delay(1, 2)
            except Exception as e:
                self.logger.error(f"Error scraping category {category_url}: {str(e)}")
        
        # Remove duplicates
        all_product_links = list(set(all_product_links))
        self.logger.info(f"Found total {len(all_product_links)} unique products")
        
        # Scrape products
        max_products = 100
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
    with BQWatchesScraper() as scraper:
        data = scraper.scrape()
        scraper.save_data("bqwatches_rolex")
        print(f"Scraped {len(data)} products from BQ Watches")
