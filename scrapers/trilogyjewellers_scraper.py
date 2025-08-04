import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_scraper import BaseScraper
import re

class TrilogyJewellersScraper(BaseScraper):
    """Scraper for TrilogyJewellers.com"""
    
    def __init__(self):
        super().__init__(
            base_url="https://trilogyjewellers.com",
            site_name="trilogyjewellers",
            use_selenium=True  # Shopify store might need JS
        )
        
        self.category_urls = [
            "https://trilogyjewellers.com/collections/rolex-watches",
            "https://trilogyjewellers.com/collections/omega-watches",
            "https://trilogyjewellers.com/collections/cartier-watches",
            "https://trilogyjewellers.com/collections/breitling-watches",
            "https://trilogyjewellers.com/collections/tudor-watches",
            "https://trilogyjewellers.com/collections/all-watches"
        ]
    
    def scrape_product_links(self, category_url: str) -> list:
        """Extract product links from Shopify collection page"""
        self.logger.info(f"Scraping product links from: {category_url}")
        
        soup = self.get_page(category_url)
        if not soup:
            return []
        
        product_links = []
        
        # Shopify product link selectors
        link_selectors = [
            '.grid-product__link',
            '.product-item a',
            'a[href*="/products/"]',
            '.product-card a'
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
        
        # Handle Shopify pagination
        pagination_info = soup.select_one('[data-collection-pagination]')
        if pagination_info:
            # Try to load more products by scrolling or checking pagination
            for page in range(2, 6):  # Check up to 5 pages
                page_url = f"{category_url}?page={page}"
                self.random_delay()
                page_soup = self.get_page(page_url)
                if not page_soup:
                    break
                
                page_links = []
                for selector in link_selectors:
                    links = page_soup.select(selector)
                    if links:
                        for link in links:
                            href = link.get('href')
                            if href and '/products/' in href:
                                full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                                page_links.append(full_url)
                        break
                
                if not page_links:
                    break
                
                product_links.extend(page_links)
        
        self.logger.info(f"Found {len(product_links)} product links")
        return product_links
    
    def scrape_product_details(self, product_url: str) -> dict:
        """Scrape Shopify product details"""
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
                'h1.product__title',
                '.product-title'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    product_data['title'] = self.clean_text(title_elem.get_text())
                    break
            
            # Extract price
            price_selectors = [
                '.product__price .money',
                '.price .money',
                '[data-product-price]'
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
                '.rte'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product_data['description'] = self.clean_text(desc_elem.get_text())
                    break
            
            # Extract images
            img_selectors = [
                '.product-single__photos img',
                '.product__media img',
                '.product-images img'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        # Handle Shopify image URLs
                        if src.startswith('//'):
                            src = f"https:{src}"
                        elif not src.startswith('http'):
                            src = f"{self.base_url}{src}"
                        
                        if src not in product_data['images']:
                            product_data['images'].append(src)
                break
            
            # Extract watch details
            watch_details = self.extract_watch_details(
                product_data['title'], 
                product_data['description']
            )
            product_data.update(watch_details)
            
            # Extract Shopify product metafields/variants
            script_tags = soup.find_all('script', type='application/json')
            for script in script_tags:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'product' in data:
                        product_info = data['product']
                        
                        # Extract vendor as brand
                        if 'vendor' in product_info:
                            product_data['brand'] = product_info['vendor']
                        
                        # Extract tags for additional info
                        if 'tags' in product_info:
                            tags = product_info['tags']
                            product_data['specifications']['tags'] = tags
                            
                            # Extract reference from tags
                            for tag in tags:
                                if re.match(r'\d{4,6}', str(tag)):
                                    product_data['reference'] = str(tag)
                                    break
                        
                        break
                except:
                    continue
            
            # Check availability
            availability_selectors = [
                '.product-form__availability',
                '.product__availability',
                '.stock-status'
            ]
            
            for selector in availability_selectors:
                avail_elem = soup.select_one(selector)
                if avail_elem:
                    product_data['availability'] = self.clean_text(avail_elem.get_text())
                    break
            
            if not product_data['availability']:
                # Check if add to cart button exists
                add_to_cart = soup.select_one('[data-add-to-cart], .btn-product-add')
                if add_to_cart:
                    if 'disabled' in add_to_cart.get('class', []):
                        product_data['availability'] = 'Out of Stock'
                    else:
                        product_data['availability'] = 'In Stock'
                else:
                    product_data['availability'] = 'Contact for Availability'
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {str(e)}")
        
        return product_data
    
    def scrape(self) -> list:
        """Main scraping method"""
        self.logger.info("Starting Trilogy Jewellers scraping...")
        
        all_product_links = []
        
        for category_url in self.category_urls:
            try:
                links = self.scrape_product_links(category_url)
                all_product_links.extend(links)
                self.random_delay(2, 3)
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
    with TrilogyJewellersScraper() as scraper:
        data = scraper.scrape()
        scraper.save_data("trilogyjewellers_watches")
        print(f"Scraped {len(data)} products from Trilogy Jewellers")
