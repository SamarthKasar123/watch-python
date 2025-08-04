import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_scraper import BaseScraper
import re

class WatchTraderScraper(BaseScraper):
    """Scraper for WatchTrader.co.uk"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.watchtrader.co.uk",
            site_name="watchtrader",
            use_selenium=False
        )
        
        self.category_urls = [
            "https://www.watchtrader.co.uk/shop/",
            "https://www.watchtrader.co.uk/shop/brand/rolex/",
            "https://www.watchtrader.co.uk/shop/brand/omega/",
            "https://www.watchtrader.co.uk/shop/brand/cartier/",
            "https://www.watchtrader.co.uk/shop/brand/breitling/"
        ]

class WatchCollectorsScraper(BaseScraper):
    """Scraper for WatchCollectors.co.uk"""
    
    def __init__(self):
        super().__init__(
            base_url="https://watchcollectors.co.uk",
            site_name="watchcollectors",
            use_selenium=True
        )
        
        self.category_urls = [
            "https://watchcollectors.co.uk/collections/all",
            "https://watchcollectors.co.uk/collections/rolex",
            "https://watchcollectors.co.uk/collections/omega",
            "https://watchcollectors.co.uk/collections/luxury-watches"
        ]

class LuxuryWatchCompanyScraper(BaseScraper):
    """Scraper for TheLuxuryWatchCompany.com"""
    
    def __init__(self):
        super().__init__(
            base_url="https://theluxurywatchcompany.com",
            site_name="luxurywatchcompany",
            use_selenium=False
        )
        
        self.category_urls = [
            "https://theluxurywatchcompany.com/product-category/mens/",
            "https://theluxurywatchcompany.com/product-category/womens/",
            "https://theluxurywatchcompany.com/product-category/luxury/"
        ]

class WatchesCoUkScraper(BaseScraper):
    """Scraper for Watches.co.uk"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.watches.co.uk",
            site_name="watches_couk",
            use_selenium=False
        )
        
        self.category_urls = [
            "https://www.watches.co.uk/mens-watches",
            "https://www.watches.co.uk/womens-watches",
            "https://www.watches.co.uk/luxury-watches"
        ]

class UKSpecialistWatchesScraper(BaseScraper):
    """Scraper for UKSpecialistWatches.co.uk"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.ukspecialistwatches.co.uk",
            site_name="ukspecialistwatches",
            use_selenium=False
        )
        
        self.category_urls = [
            "https://www.ukspecialistwatches.co.uk/shop/",
            "https://www.ukspecialistwatches.co.uk/shop/rolex/",
            "https://www.ukspecialistwatches.co.uk/shop/omega/"
        ]

class WatchBuyersScraper(BaseScraper):
    """Scraper for WatchBuyers.co.uk"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.watchbuyers.co.uk",
            site_name="watchbuyers",
            use_selenium=False
        )
        
        self.category_urls = [
            "https://www.watchbuyers.co.uk/watches-for-sale-c12",
            "https://www.watchbuyers.co.uk/rolex-c13",
            "https://www.watchbuyers.co.uk/omega-c14"
        ]

class WatchTheTimeScraper(BaseScraper):
    """Scraper for WatchTheTime.co.uk"""
    
    def __init__(self):
        super().__init__(
            base_url="https://watchthetime.co.uk",
            site_name="watchthetime",
            use_selenium=True
        )
        
        self.category_urls = [
            "https://watchthetime.co.uk/collections/all-items",
            "https://watchthetime.co.uk/collections/rolex",
            "https://watchthetime.co.uk/collections/omega"
        ]

# Generic implementation for all these scrapers
class GenericWatchScraper(BaseScraper):
    """Generic scraper that can be configured for different watch websites"""
    
    def __init__(self, site_config):
        super().__init__(
            base_url=site_config['base_url'],
            site_name=site_config['site_name'],
            use_selenium=site_config.get('use_selenium', False)
        )
        
        self.category_urls = site_config['category_urls']
        self.selectors = site_config.get('selectors', self.get_default_selectors())
    
    def get_default_selectors(self):
        """Default selectors for common e-commerce platforms"""
        return {
            'product_links': [
                'a[href*="/products/"]',  # Shopify
                'a[href*="/product/"]',   # WooCommerce
                '.product a',
                '.product-item a',
                '.woocommerce-loop-product__link'
            ],
            'title': [
                '.product_title',
                '.product__title',
                'h1.product-title',
                '.product-single__title'
            ],
            'price': [
                '.price .amount',
                '.price .money',
                '.product__price',
                '.woocommerce-Price-amount'
            ],
            'description': [
                '.product__description',
                '.product-description',
                '.woocommerce-product-details__short-description'
            ],
            'images': [
                '.product-images img',
                '.product__media img',
                '.woocommerce-product-gallery__image img'
            ]
        }
    
    def scrape_product_links(self, category_url: str) -> list:
        """Generic product link extraction"""
        self.logger.info(f"Scraping product links from: {category_url}")
        
        soup = self.get_page(category_url)
        if not soup:
            return []
        
        product_links = []
        
        for selector in self.selectors['product_links']:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href and ('/product' in href):
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        if full_url not in product_links:
                            product_links.append(full_url)
                break
        
        self.logger.info(f"Found {len(product_links)} product links")
        return product_links
    
    def scrape_product_details(self, product_url: str) -> dict:
        """Generic product detail extraction"""
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
            for selector in self.selectors['title']:
                title_elem = soup.select_one(selector)
                if title_elem:
                    product_data['title'] = self.clean_text(title_elem.get_text())
                    break
            
            # Extract price
            for selector in self.selectors['price']:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text()
                    product_data['price'] = self.extract_price(price_text)
                    if product_data['price']:
                        break
            
            # Extract description
            for selector in self.selectors['description']:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product_data['description'] = self.clean_text(desc_elem.get_text())
                    break
            
            # Extract images
            for selector in self.selectors['images']:
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
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {str(e)}")
        
        return product_data
    
    def scrape(self) -> list:
        """Main scraping method"""
        self.logger.info(f"Starting {self.site_name} scraping...")
        
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
        
        # Scrape products (limit for efficiency)
        max_products = 50  # Reduced for each site
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


# Site configurations
SITE_CONFIGS = {
    'watchtrader': {
        'base_url': 'https://www.watchtrader.co.uk',
        'site_name': 'watchtrader',
        'use_selenium': False,
        'category_urls': [
            'https://www.watchtrader.co.uk/shop/',
            'https://www.watchtrader.co.uk/shop/brand/rolex/',
            'https://www.watchtrader.co.uk/shop/brand/omega/'
        ]
    },
    'watchcollectors': {
        'base_url': 'https://watchcollectors.co.uk',
        'site_name': 'watchcollectors',
        'use_selenium': True,
        'category_urls': [
            'https://watchcollectors.co.uk/collections/all',
            'https://watchcollectors.co.uk/collections/rolex'
        ]
    },
    'luxurywatchcompany': {
        'base_url': 'https://theluxurywatchcompany.com',
        'site_name': 'luxurywatchcompany',
        'use_selenium': False,
        'category_urls': [
            'https://theluxurywatchcompany.com/product-category/mens/',
            'https://theluxurywatchcompany.com/product-category/luxury/'
        ]
    },
    'watches_couk': {
        'base_url': 'https://www.watches.co.uk',
        'site_name': 'watches_couk',
        'use_selenium': False,
        'category_urls': [
            'https://www.watches.co.uk/mens-watches',
            'https://www.watches.co.uk/luxury-watches'
        ]
    },
    'ukspecialistwatches': {
        'base_url': 'https://www.ukspecialistwatches.co.uk',
        'site_name': 'ukspecialistwatches',
        'use_selenium': False,
        'category_urls': [
            'https://www.ukspecialistwatches.co.uk/shop/',
            'https://www.ukspecialistwatches.co.uk/shop/rolex/'
        ]
    },
    'watchbuyers': {
        'base_url': 'https://www.watchbuyers.co.uk',
        'site_name': 'watchbuyers',
        'use_selenium': False,
        'category_urls': [
            'https://www.watchbuyers.co.uk/watches-for-sale-c12'
        ]
    },
    'watchthetime': {
        'base_url': 'https://watchthetime.co.uk',
        'site_name': 'watchthetime',
        'use_selenium': True,
        'category_urls': [
            'https://watchthetime.co.uk/collections/all-items'
        ]
    }
}

if __name__ == "__main__":
    import sys
    
    site_name = sys.argv[1] if len(sys.argv) > 1 else 'watchtrader'
    
    if site_name in SITE_CONFIGS:
        config = SITE_CONFIGS[site_name]
        with GenericWatchScraper(config) as scraper:
            data = scraper.scrape()
            scraper.save_data(f"{site_name}_watches")
            print(f"Scraped {len(data)} products from {site_name}")
    else:
        print(f"Available sites: {list(SITE_CONFIGS.keys())}")
