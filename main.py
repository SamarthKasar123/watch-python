"""
Main script to execute all watch scrapers and consolidate data
"""

import os
import sys
import time
import pandas as pd
import json
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.chronofinder_scraper import ChronoFinderScraper
from scrapers.prestigiousjewellers_scraper import PrestigiousJewellersScraper
from scrapers.bqwatches_scraper import BQWatchesScraper
from scrapers.trilogyjewellers_scraper import TrilogyJewellersScraper
from scrapers.additional_scrapers import GenericWatchScraper, SITE_CONFIGS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watch_scraping.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class WatchScrapingManager:
    """Manages the execution of all watch scrapers"""
    
    def __init__(self):
        self.scrapers = {
            'chronofinder': ChronoFinderScraper,
            'prestigiousjewellers': PrestigiousJewellersScraper,
            'bqwatches': BQWatchesScraper,
            'trilogyjewellers': TrilogyJewellersScraper
        }
        
        # Add generic scrapers
        for site_name, config in SITE_CONFIGS.items():
            self.scrapers[site_name] = lambda config=config: GenericWatchScraper(config)
        
        self.all_data = []
        self.results = {}
    
    def run_single_scraper(self, scraper_name: str, scraper_class) -> dict:
        """Run a single scraper and return results"""
        start_time = time.time()
        result = {
            'name': scraper_name,
            'success': False,
            'data_count': 0,
            'execution_time': 0,
            'error': None
        }
        
        try:
            logger.info(f"Starting scraper: {scraper_name}")
            
            with scraper_class() as scraper:
                data = scraper.scrape()
                scraper.save_data(f"{scraper_name}_watches_{int(time.time())}")
                
                result['success'] = True
                result['data_count'] = len(data)
                result['data'] = data
                
                logger.info(f"Completed {scraper_name}: {len(data)} products")
                
        except Exception as e:
            error_msg = f"Error in {scraper_name}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
        
        result['execution_time'] = time.time() - start_time
        return result
    
    def run_all_scrapers(self, parallel: bool = False, selected_scrapers: list = None):
        """Run all scrapers either in parallel or sequentially"""
        scrapers_to_run = selected_scrapers or list(self.scrapers.keys())
        
        logger.info(f"Starting to scrape {len(scrapers_to_run)} websites...")
        
        if parallel:
            self.run_parallel(scrapers_to_run)
        else:
            self.run_sequential(scrapers_to_run)
        
        self.consolidate_data()
        self.generate_report()
    
    def run_sequential(self, scrapers_to_run: list):
        """Run scrapers one by one"""
        for scraper_name in scrapers_to_run:
            if scraper_name in self.scrapers:
                scraper_class = self.scrapers[scraper_name]
                result = self.run_single_scraper(scraper_name, scraper_class)
                self.results[scraper_name] = result
                
                if result['success']:
                    self.all_data.extend(result['data'])
                
                # Add delay between scrapers to be respectful
                time.sleep(5)
    
    def run_parallel(self, scrapers_to_run: list):
        """Run scrapers in parallel (use with caution)"""
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_scraper = {}
            
            for scraper_name in scrapers_to_run:
                if scraper_name in self.scrapers:
                    scraper_class = self.scrapers[scraper_name]
                    future = executor.submit(self.run_single_scraper, scraper_name, scraper_class)
                    future_to_scraper[future] = scraper_name
            
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                try:
                    result = future.result()
                    self.results[scraper_name] = result
                    
                    if result['success']:
                        self.all_data.extend(result['data'])
                        
                except Exception as e:
                    logger.error(f"Parallel execution error for {scraper_name}: {str(e)}")
    
    def consolidate_data(self):
        """Consolidate all scraped data into unified format"""
        if not self.all_data:
            logger.warning("No data to consolidate")
            return
        
        logger.info(f"Consolidating {len(self.all_data)} products...")
        
        # Create DataFrame
        df = pd.DataFrame(self.all_data)
        
        # Clean and standardize data
        df = self.clean_dataframe(df)
        
        # Save consolidated data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as CSV
        csv_file = f"data/consolidated_watches_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        
        # Save as JSON
        json_file = f"data/consolidated_watches_{timestamp}.json"
        df.to_json(json_file, orient='records', indent=2)
        
        # Save as Excel with multiple sheets
        excel_file = f"data/consolidated_watches_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            df.to_excel(writer, sheet_name='All_Watches', index=False)
            
            # Create separate sheets by brand
            for brand in df['brand'].dropna().unique():
                brand_df = df[df['brand'] == brand]
                if len(brand_df) > 0:
                    sheet_name = brand.replace(' ', '_')[:31]  # Excel sheet name limit
                    brand_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Create separate sheets by site
            for site in df['site'].unique():
                site_df = df[df['site'] == site]
                if len(site_df) > 0:
                    sheet_name = site[:31]
                    site_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Consolidated data saved to {csv_file}, {json_file}, and {excel_file}")
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the dataframe"""
        # Remove duplicates based on URL
        df = df.drop_duplicates(subset=['url'], keep='first')
        
        # Clean text fields
        text_fields = ['title', 'brand', 'model', 'description']
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].astype(str).str.strip()
                df[field] = df[field].replace('nan', '')
        
        # Standardize price format
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # Add derived fields
        df['scrape_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Price categories
        if 'price' in df.columns:
            df['price_category'] = pd.cut(
                df['price'], 
                bins=[0, 1000, 5000, 10000, 25000, 50000, float('inf')],
                labels=['Under £1K', '£1K-£5K', '£5K-£10K', '£10K-£25K', '£25K-£50K', 'Over £50K']
            )
        
        return df
    
    def generate_report(self):
        """Generate a summary report of the scraping results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = {
            'scraping_summary': {
                'timestamp': timestamp,
                'total_sites_attempted': len(self.results),
                'successful_sites': len([r for r in self.results.values() if r['success']]),
                'total_products_scraped': len(self.all_data),
                'execution_details': self.results
            }
        }
        
        # Site-wise summary
        site_summary = {}
        for site_name, result in self.results.items():
            site_summary[site_name] = {
                'success': result['success'],
                'products_count': result['data_count'],
                'execution_time_seconds': round(result['execution_time'], 2),
                'error': result.get('error')
            }
        
        report['site_summary'] = site_summary
        
        # Product analysis
        if self.all_data:
            df = pd.DataFrame(self.all_data)
            
            # Brand distribution
            brand_counts = df['brand'].value_counts().to_dict()
            report['brand_distribution'] = brand_counts
            
            # Price analysis
            if 'price' in df.columns:
                price_stats = df['price'].describe().to_dict()
                report['price_statistics'] = {k: round(v, 2) if pd.notna(v) else None for k, v in price_stats.items()}
            
            # Site distribution
            site_counts = df['site'].value_counts().to_dict()
            report['site_distribution'] = site_counts
        
        # Save report
        report_file = f"data/scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*50)
        print("WATCH SCRAPING SUMMARY")
        print("="*50)
        print(f"Timestamp: {timestamp}")
        print(f"Sites Attempted: {report['scraping_summary']['total_sites_attempted']}")
        print(f"Successful Sites: {report['scraping_summary']['successful_sites']}")
        print(f"Total Products: {report['scraping_summary']['total_products_scraped']}")
        print("\nSite Results:")
        for site, details in site_summary.items():
            status = "✓" if details['success'] else "✗"
            print(f"  {status} {site}: {details['products_count']} products ({details['execution_time_seconds']}s)")
            if details['error']:
                print(f"    Error: {details['error']}")
        
        if 'brand_distribution' in report:
            print(f"\nTop Brands:")
            for brand, count in list(report['brand_distribution'].items())[:5]:
                print(f"  {brand}: {count} products")
        
        print(f"\nDetailed report saved to: {report_file}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Watch Scraping Tool')
    parser.add_argument('--sites', nargs='+', help='Specific sites to scrape')
    parser.add_argument('--parallel', action='store_true', help='Run scrapers in parallel')
    parser.add_argument('--list-sites', action='store_true', help='List available sites')
    
    args = parser.parse_args()
    
    manager = WatchScrapingManager()
    
    if args.list_sites:
        print("Available sites:")
        for site in manager.scrapers.keys():
            print(f"  - {site}")
        return
    
    try:
        manager.run_all_scrapers(
            parallel=args.parallel,
            selected_scrapers=args.sites
        )
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
