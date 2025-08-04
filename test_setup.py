"""
Test script to verify the watch scraping setup
"""

import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from utils.base_scraper import BaseScraper
        print("✓ Base scraper imported successfully")
    except Exception as e:
        print(f"✗ Error importing base scraper: {e}")
        return False
    
    try:
        from scrapers.chronofinder_scraper import ChronoFinderScraper
        print("✓ ChronoFinder scraper imported successfully")
    except Exception as e:
        print(f"✗ Error importing ChronoFinder scraper: {e}")
    
    try:
        from scrapers.prestigiousjewellers_scraper import PrestigiousJewellersScraper
        print("✓ PrestigiousJewellers scraper imported successfully")
    except Exception as e:
        print(f"✗ Error importing PrestigiousJewellers scraper: {e}")
    
    try:
        from utils.data_processor import WatchDataProcessor
        print("✓ Data processor imported successfully")
    except Exception as e:
        print(f"✗ Error importing data processor: {e}")
    
    try:
        from config.settings import config
        print("✓ Configuration imported successfully")
    except Exception as e:
        print(f"✗ Error importing configuration: {e}")
    
    return True

def test_basic_scraping():
    """Test basic scraping functionality"""
    print("\nTesting basic scraping...")
    
    try:
        from utils.base_scraper import BaseScraper
        
        # Test creating a basic scraper
        scraper = BaseScraper(
            base_url="https://httpbin.org",
            site_name="test_site",
            use_selenium=False
        )
        
        # Test making a simple request
        soup = scraper.get_page("https://httpbin.org/html")
        if soup:
            print("✓ Basic HTTP request successful")
        else:
            print("✗ Basic HTTP request failed")
        
        # Test price extraction
        test_prices = ["£1,250.00", "$2,500", "€1,800.50", "1500"]
        for price_text in test_prices:
            extracted = scraper.extract_price(price_text)
            print(f"  Price '{price_text}' -> {extracted}")
        
        scraper.cleanup()
        print("✓ Basic scraping test completed")
        
    except Exception as e:
        print(f"✗ Error in basic scraping test: {e}")

def test_data_processing():
    """Test data processing functionality"""
    print("\nTesting data processing...")
    
    try:
        from utils.data_processor import WatchDataProcessor
        
        # Create test data
        test_data = [
            {
                'title': 'Rolex Submariner 116610LN',
                'brand': 'Rolex',
                'model': 'Submariner',
                'reference': '116610LN',
                'price': 8500,
                'site': 'test_site'
            },
            {
                'title': 'Omega Speedmaster Professional',
                'brand': 'Omega',
                'model': 'Speedmaster',
                'reference': '311.30.42.30.01.005',
                'price': 3200,
                'site': 'test_site'
            }
        ]
        
        # Test data processor
        processor = WatchDataProcessor()
        import pandas as pd
        processor.df = pd.DataFrame(test_data)
        
        stats = processor.generate_statistics()
        print(f"✓ Generated statistics: {stats['total_watches']} watches")
        
        # Test similarity matching
        test_watch = {
            'title': 'Rolex Submariner Black',
            'brand': 'Rolex',
            'model': 'Submariner',
            'reference': '116610LN'
        }
        
        similar = processor.find_similar_watches(test_watch)
        print(f"✓ Found {len(similar)} similar watches")
        
    except Exception as e:
        print(f"✗ Error in data processing test: {e}")

def test_configuration():
    """Test configuration settings"""
    print("\nTesting configuration...")
    
    try:
        from config.settings import config
        
        enabled_sites = config.get_enabled_sites()
        print(f"✓ Configuration loaded. {len(enabled_sites)} sites enabled")
        
        print("Enabled sites:")
        for site in enabled_sites[:5]:  # Show first 5
            print(f"  - {site}")
        
        if config.TARGET_BRANDS:
            print(f"✓ {len(config.TARGET_BRANDS)} target brands configured")
        
    except Exception as e:
        print(f"✗ Error in configuration test: {e}")

def test_sample_scraper():
    """Test a sample scraper with minimal data"""
    print("\nTesting sample scraper (ChronoFinder)...")
    
    try:
        from scrapers.chronofinder_scraper import ChronoFinderScraper
        
        # Create scraper instance
        scraper = ChronoFinderScraper()
        
        # Test getting a single page
        test_url = "https://chronofinder.com"
        soup = scraper.get_page(test_url, use_selenium=False)
        
        if soup:
            print("✓ Successfully connected to ChronoFinder")
            title = soup.find('title')
            if title:
                print(f"  Page title: {title.get_text()[:50]}...")
        else:
            print("✗ Could not connect to ChronoFinder")
        
        scraper.cleanup()
        
    except Exception as e:
        print(f"✗ Error testing sample scraper: {e}")

def run_quick_test():
    """Run a quick test of a single scraper"""
    print("\nRunning quick scraper test...")
    
    try:
        from scrapers.additional_scrapers import GenericWatchScraper, SITE_CONFIGS
        
        # Test with a simple site configuration
        test_config = {
            'base_url': 'https://httpbin.org',
            'site_name': 'test_scraper',
            'use_selenium': False,
            'category_urls': ['https://httpbin.org/html']
        }
        
        with GenericWatchScraper(test_config) as scraper:
            print("✓ Generic scraper created successfully")
            
            # Test basic functionality
            soup = scraper.get_page('https://httpbin.org/html')
            if soup:
                print("✓ Generic scraper can fetch pages")
            
        print("✓ Quick scraper test completed")
        
    except Exception as e:
        print(f"✗ Error in quick scraper test: {e}")

def main():
    """Run all tests"""
    print("=" * 50)
    print("WATCH SCRAPING TOOL - SETUP TEST")
    print("=" * 50)
    
    start_time = time.time()
    
    # Run tests
    test_imports()
    test_configuration()
    test_basic_scraping()
    test_data_processing()
    test_sample_scraper()
    run_quick_test()
    
    execution_time = time.time() - start_time
    
    print("\n" + "=" * 50)
    print(f"Tests completed in {execution_time:.2f} seconds")
    print("=" * 50)
    
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run a single scraper: python scrapers/chronofinder_scraper.py")
    print("3. Run all scrapers: python main.py")
    print("4. Run specific sites: python main.py --sites chronofinder bqwatches")
    print("5. List available sites: python main.py --list-sites")

if __name__ == "__main__":
    main()
