"""
Configuration settings for the watch scraping tool
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for watch scraping tool"""
    
    # API Settings
    WOOCOMMERCE_URL = os.getenv('WOOCOMMERCE_URL', '')
    WOOCOMMERCE_CONSUMER_KEY = os.getenv('WOOCOMMERCE_CONSUMER_KEY', '')
    WOOCOMMERCE_CONSUMER_SECRET = os.getenv('WOOCOMMERCE_CONSUMER_SECRET', '')
    
    SHOPIFY_SHOP_NAME = os.getenv('SHOPIFY_SHOP_NAME', '')
    SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
    SHOPIFY_API_VERSION = os.getenv('SHOPIFY_API_VERSION', '2023-10')
    
    # Scraping Settings
    MAX_PRODUCTS_PER_SITE = int(os.getenv('MAX_PRODUCTS_PER_SITE', '100'))
    DELAY_BETWEEN_REQUESTS = float(os.getenv('DELAY_BETWEEN_REQUESTS', '2.0'))
    USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
    PROXY_URL = os.getenv('PROXY_URL', '')
    
    # File Paths
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    LOG_FILE = os.path.join(DATA_DIR, 'watch_scraping.log')
    
    # Target Sites Configuration
    TARGET_SITES = {
        'chronofinder': {
            'base_url': 'https://chronofinder.com',
            'enabled': True,
            'priority': 1,
            'use_selenium': True,
            'max_products': 100
        },
        'prestigiousjewellers': {
            'base_url': 'https://www.prestigiousjewellers.com',
            'enabled': True,
            'priority': 2,
            'use_selenium': False,
            'max_products': 100
        },
        'bqwatches': {
            'base_url': 'https://www.bqwatches.com',
            'enabled': True,
            'priority': 3,
            'use_selenium': False,
            'max_products': 100
        },
        'trilogyjewellers': {
            'base_url': 'https://trilogyjewellers.com',
            'enabled': True,
            'priority': 4,
            'use_selenium': True,
            'max_products': 100
        },
        'watchtrader': {
            'base_url': 'https://www.watchtrader.co.uk',
            'enabled': True,
            'priority': 5,
            'use_selenium': False,
            'max_products': 50
        },
        'watchcollectors': {
            'base_url': 'https://watchcollectors.co.uk',
            'enabled': True,
            'priority': 6,
            'use_selenium': True,
            'max_products': 50
        },
        'luxurywatchcompany': {
            'base_url': 'https://theluxurywatchcompany.com',
            'enabled': True,
            'priority': 7,
            'use_selenium': False,
            'max_products': 50
        },
        'watches_couk': {
            'base_url': 'https://www.watches.co.uk',
            'enabled': True,
            'priority': 8,
            'use_selenium': False,
            'max_products': 50
        },
        'ukspecialistwatches': {
            'base_url': 'https://www.ukspecialistwatches.co.uk',
            'enabled': True,
            'priority': 9,
            'use_selenium': False,
            'max_products': 50
        },
        'watchbuyers': {
            'base_url': 'https://www.watchbuyers.co.uk',
            'enabled': True,
            'priority': 10,
            'use_selenium': False,
            'max_products': 50
        },
        'watchthetime': {
            'base_url': 'https://watchthetime.co.uk',
            'enabled': True,
            'priority': 11,
            'use_selenium': True,
            'max_products': 50
        }
    }
    
    # Price Comparison Settings
    PRICE_COMPARISON = {
        'default_discount': 100,  # £100 below competitor price
        'min_price_difference': 50,  # Minimum difference to suggest price change
        'max_price_increase': 0.2,  # Maximum 20% price increase
        'max_price_decrease': 0.3   # Maximum 30% price decrease
    }
    
    # Matching Settings
    MATCHING = {
        'similarity_threshold': 0.8,
        'brand_weight': 0.4,
        'reference_weight': 0.3,
        'model_weight': 0.2,
        'title_weight': 0.1
    }
    
    # Watch Brands to Focus On
    TARGET_BRANDS = [
        'Rolex',
        'Omega',
        'Patek Philippe',
        'Audemars Piguet',
        'Cartier',
        'Breitling',
        'TAG Heuer',
        'Tudor',
        'IWC',
        'Jaeger-LeCoultre',
        'Vacheron Constantin',
        'Richard Mille'
    ]
    
    @classmethod
    def get_enabled_sites(cls):
        """Get list of enabled sites sorted by priority"""
        enabled_sites = []
        for site_name, config in cls.TARGET_SITES.items():
            if config.get('enabled', True):
                enabled_sites.append((site_name, config))
        
        # Sort by priority
        enabled_sites.sort(key=lambda x: x[1].get('priority', 999))
        return [site[0] for site in enabled_sites]
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check if data directory exists
        if not os.path.exists(cls.DATA_DIR):
            try:
                os.makedirs(cls.DATA_DIR)
            except Exception as e:
                errors.append(f"Cannot create data directory: {e}")
        
        # Validate API settings if provided
        if cls.WOOCOMMERCE_URL and not cls.WOOCOMMERCE_CONSUMER_KEY:
            errors.append("WooCommerce URL provided but missing consumer key")
        
        if cls.SHOPIFY_SHOP_NAME and not cls.SHOPIFY_ACCESS_TOKEN:
            errors.append("Shopify shop name provided but missing access token")
        
        return errors

# Global config instance
config = Config()

# Validate configuration on import
validation_errors = config.validate_config()
if validation_errors:
    print("Configuration warnings:")
    for error in validation_errors:
        print(f"  - {error}")

# Export commonly used settings
__all__ = ['config', 'Config']
