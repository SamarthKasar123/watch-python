import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_scraper import BaseScraper
import re

class PrestigiousJewellersScraper(BaseScraper):
    """Scraper for PrestigiousJewellers.com"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.prestigiousjewellers.com",
            site_name="prestigiousjewellers",
            use_selenium=False
        )
        
        self.category_urls = [
            "https://www.prestigiousjewellers.com/product-category/watches/",
            "https://www.prestigiousjewellers.com/product-category/watches/rolex/",
            "https://www.prestigiousjewellers.com/product-category/watches/omega/",
            "https://www.prestigiousjewellers.com/product-category/watches/cartier/",
            "https://www.prestigiousjewellers.com/product-category/watches/breitling/"
        ]
    
    def scrape_product_links(self, category_url: str) -> list:
        """Extract all product links from category page"""
        self.logger.info(f"Scraping product links from: {category_url}")
        
        soup = self.get_page(category_url)
        if not soup:
            return []
        
        product_links = []
        
        # WooCommerce product links
        link_selectors = [
            '.woocommerce-loop-product__link',
            '.product .woocommerce-LoopProduct-link',
            'a[href*="/product/"]',
            '.products .product a'
        ]
        
        for selector in link_selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        if full_url not in product_links:
                            product_links.append(full_url)
                break
        
        # Handle pagination
        page_num = 2
        while page_num <= 5:  # Limit pagination
            page_url = f"{category_url}page/{page_num}/"
            page_soup = self.get_page(page_url)
            if not page_soup:
                break
            
            page_links = []
            for selector in link_selectors:
                links = page_soup.select(selector)
                if links:
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                            page_links.append(full_url)
                    break
            
            if not page_links:
                break
            
            product_links.extend(page_links)
            page_num += 1
            self.random_delay()
        
        self.logger.info(f"Found {len(product_links)} product links")
        return product_links
    
    def scrape_product_details(self, product_url: str) -> dict:
        """Scrape product details from WooCommerce product page"""
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
                '.product_title.entry-title',
                'h1.product_title',
                '.summary .product_title'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    product_data['title'] = self.clean_text(title_elem.get_text())
                    break
            
            # Extract price
            price_selectors = [
                '.price .woocommerce-Price-amount',
                '.price ins .woocommerce-Price-amount',
                '.price .amount',
                '.summary .price'
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
                '.product_meta',
                '.woocommerce-Tabs-panel--description'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product_data['description'] = self.clean_text(desc_elem.get_text())
                    break
            
            # Extract images
            img_selectors = [
                '.woocommerce-product-gallery__image img',
                '.product-images img',
                '.wp-post-image'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-large_image')
                    if src:
                        img_url = src if src.startswith('http') else f"{self.base_url}{src}"
                        if img_url not in product_data['images']:
                            product_data['images'].append(img_url)
            
            # Extract specifications from product meta
            meta_elem = soup.select_one('.product_meta')
            if meta_elem:
                meta_text = meta_elem.get_text()
                product_data['specifications']['meta'] = self.clean_text(meta_text)
            
            # Extract watch details
            watch_details = self.extract_watch_details(
                product_data['title'], 
                product_data['description']
            )
            product_data.update(watch_details)
            
            # Check stock status
            stock_elem = soup.select_one('.stock')
            if stock_elem:
                stock_text = stock_elem.get_text().lower()
                if 'in stock' in stock_text:
                    product_data['availability'] = 'In Stock'
                elif 'out of stock' in stock_text:
                    product_data['availability'] = 'Out of Stock'
                else:
                    product_data['availability'] = self.clean_text(stock_elem.get_text())
            
            # Extract additional specifications from tabs
            specs_tab = soup.select_one('#tab-additional_information')
            if specs_tab:
                specs_table = specs_tab.select('table tr')
                for row in specs_table:
                    cells = row.select('td')
                    if len(cells) == 2:
                        key = self.clean_text(cells[0].get_text()).lower()
                        value = self.clean_text(cells[1].get_text())
                        product_data['specifications'][key] = value
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {str(e)}")
        
        return product_data
    
    def scrape(self) -> list:
        """Main scraping method"""
        self.logger.info("Starting PrestigiousJewellers scraping...")
        
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
    with PrestigiousJewellersScraper() as scraper:
        data = scraper.scrape()
        scraper.save_data("prestigiousjewellers_watches")
        print(f"Scraped {len(data)} products from PrestigiousJewellers")
