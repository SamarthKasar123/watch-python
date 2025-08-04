import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import random
from fake_useragent import UserAgent
import json
import csv
import pandas as pd
import re
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Any, Optional

class BaseScraper:
    """Base class for all watch website scrapers"""
    
    def __init__(self, base_url: str, site_name: str, use_selenium: bool = False):
        self.base_url = base_url
        self.site_name = site_name
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.ua = UserAgent()
        self.driver = None
        self.scraped_data = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"{site_name}_scraper")
        
        # Setup session headers
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def setup_driver(self):
        """Setup Selenium WebDriver with stealth options"""
        if self.driver:
            return self.driver
            
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
        # Uncomment for headless mode
        # chrome_options.add_argument('--headless')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    def get_page(self, url: str, use_selenium: bool = None) -> Optional[BeautifulSoup]:
        """Get page content using requests or selenium"""
        if use_selenium is None:
            use_selenium = self.use_selenium
            
        try:
            if use_selenium:
                if not self.driver:
                    self.setup_driver()
                
                self.driver.get(url)
                time.sleep(random.uniform(2, 4))
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                html = self.driver.page_source
                return BeautifulSoup(html, 'html.parser')
            else:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
                
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay between requests"""
        time.sleep(random.uniform(min_delay, max_delay))
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numerical price from text"""
        if not price_text:
            return None
            
        # Remove currency symbols and clean text
        price_clean = re.sub(r'[£$€,\s]', '', price_text.strip())
        
        # Extract numbers (including decimals)
        price_match = re.search(r'(\d+(?:\.\d{2})?)', price_clean)
        
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                return None
        
        return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        return ' '.join(text.strip().split())
    
    def extract_watch_details(self, title: str, description: str = "") -> Dict[str, str]:
        """Extract watch details from title and description"""
        details = {
            'brand': '',
            'model': '',
            'reference': '',
            'year': '',
            'condition': '',
            'dial_color': '',
            'bracelet_material': '',
            'case_material': '',
            'movement': ''
        }
        
        text = f"{title} {description}".lower()
        
        # Common watch brands
        brands = ['rolex', 'omega', 'patek philippe', 'audemars piguet', 'cartier', 
                 'breitling', 'tag heuer', 'tudor', 'seiko', 'tissot', 'hamilton']
        
        for brand in brands:
            if brand in text:
                details['brand'] = brand.title()
                break
        
        # Extract reference number (common patterns)
        ref_patterns = [
            r'ref[:\.\s]*(\w+)',
            r'reference[:\.\s]*(\w+)',
            r'\b(\d{4,6}[a-zA-Z]*)\b'
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text)
            if match:
                details['reference'] = match.group(1).upper()
                break
        
        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            details['year'] = year_match.group(0)
        
        # Extract condition
        conditions = ['new', 'unworn', 'excellent', 'very good', 'good', 'fair', 'poor']
        for condition in conditions:
            if condition in text:
                details['condition'] = condition.title()
                break
        
        return details
    
    def save_data(self, filename: str = None):
        """Save scraped data to CSV and JSON"""
        if not self.scraped_data:
            self.logger.warning("No data to save")
            return
        
        if not filename:
            filename = f"{self.site_name}_{int(time.time())}"
        
        # Create data directory path (absolute)
        import os
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Save as CSV
        df = pd.DataFrame(self.scraped_data)
        csv_path = os.path.join(data_dir, f"{filename}.csv")
        df.to_csv(csv_path, index=False)
        
        # Save as JSON
        json_path = os.path.join(data_dir, f"{filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(self.scraped_data)} items to {csv_path} and {json_path}")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement the scrape method")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        
        if self.session:
            self.session.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
