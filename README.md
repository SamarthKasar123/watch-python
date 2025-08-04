# Watch Scraping & Price Comparison Tool

A comprehensive tool for scraping watch data from competitor websites and comparing prices for WooCommerce and Shopify stores.

## Features

### Price Comparison
- Pull ~900 products from WooCommerce + Shopify stores
- Match watches by model, year, dial, and bracelet on Chrono24 + Google Shopping
- Recommend new pricing (e.g., £100 below cheapest match)
- Show percentage differences and competitor links
- API integration for price updates
- Automated runs every 3 weeks or manual execution

### Competitor Scraping
- Scrape competitor websites for watch listings
- Collect product info, images, and URLs
- Match listings with existing inventory
- Identify new products not in stores
- One-click addition to WooCommerce/Shopify

## Competitor Sites
- chronofinder.com
- prestigiousjewellers.com
- bqwatches.com
- trilogyjewellers.com
- watchtrader.co.uk
- watchcollectors.co.uk
- theluxurywatchcompany.com
- watches.co.uk
- ukspecialistwatches.co.uk
- watchbuyers.co.uk
- watchthetime.co.uk

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run All Scrapers
```bash
python main.py
```

### Run Individual Scrapers
```bash
python scrapers/chronofinder_scraper.py
python scrapers/prestigiousjewellers_scraper.py
# etc.
```

## Project Structure

```
watch-scrapping/
├── scrapers/           # Individual site scrapers
├── utils/             # Utility functions
├── data/              # Scraped data storage
├── config/            # Configuration files
├── dashboard/         # Web dashboard
├── api/               # API integrations
└── main.py           # Main execution script
```

## Configuration

Create a `.env` file with your API keys:

```
WOOCOMMERCE_URL=your_store_url
WOOCOMMERCE_KEY=your_consumer_key
WOOCOMMERCE_SECRET=your_consumer_secret
SHOPIFY_SHOP=your_shop_name
SHOPIFY_ACCESS_TOKEN=your_access_token
```
