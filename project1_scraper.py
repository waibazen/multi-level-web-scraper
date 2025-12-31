# multi_level_scraper.py
"""
Multi-Level Web Scraper
Extracts product data from multiple pages and exports to CSV
Demonstrates: BeautifulSoup, requests, pagination handling, error handling
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MultiLevelScraper:
    def __init__(self, base_url, delay=1):
        """
        Initialize scraper with base URL and delay between requests
        
        Args:
            base_url (str): The website's base URL
            delay (int): Seconds to wait between requests (rate limiting)
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_page(self, url):
        """Fetch page with error handling and retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                logging.info(f"Successfully fetched: {url}")
                return response.text
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
                time.sleep(self.delay * 2)
        
    def parse_listing_page(self, html):
        """
        Parse main listing page to extract item links
        
        Returns:
            list: URLs of individual item pages
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Example: Extract links from product listings
        # Adjust selectors based on actual website structure
        item_links = []
        items = soup.find_all('div', class_='product-item')
        
        for item in items:
            link = item.find('a', href=True)
            if link:
                full_url = self.base_url + link['href'] if not link['href'].startswith('http') else link['href']
                item_links.append(full_url)
        
        logging.info(f"Found {len(item_links)} items on page")
        return item_links
    
    def parse_item_page(self, html, url):
        """
        Parse individual item page to extract details
        
        Returns:
            dict: Item data
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract data - adjust selectors for actual website
        data = {
            'url': url,
            'title': self.safe_extract(soup, 'h1', class_='product-title'),
            'price': self.safe_extract(soup, 'span', class_='price'),
            'description': self.safe_extract(soup, 'div', class_='description'),
            'rating': self.safe_extract(soup, 'span', class_='rating'),
            'availability': self.safe_extract(soup, 'span', class_='stock'),
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return data
    
    def safe_extract(self, soup, tag, **kwargs):
        """Safely extract text from element, return None if not found"""
        element = soup.find(tag, **kwargs)
        return element.get_text(strip=True) if element else None
    
    def get_next_page_url(self, soup):
        """Extract next page URL from pagination"""
        next_button = soup.find('a', class_='next-page')
        if next_button and next_button.get('href'):
            return self.base_url + next_button['href']
        return None
    
    def scrape(self, start_url, max_pages=5):
        """
        Main scraping method - crawls multiple pages
        
        Args:
            start_url (str): Starting URL
            max_pages (int): Maximum number of listing pages to scrape
            
        Returns:
            pd.DataFrame: Scraped data
        """
        all_data = []
        current_url = start_url
        page_count = 0
        
        while current_url and page_count < max_pages:
            logging.info(f"Scraping page {page_count + 1}: {current_url}")
            
            # Fetch listing page
            html = self.fetch_page(current_url)
            if not html:
                break
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Get item links from listing page
            item_links = self.parse_listing_page(html)
            
            # Scrape each item page
            for link in item_links:
                time.sleep(self.delay)  # Rate limiting
                
                item_html = self.fetch_page(link)
                if item_html:
                    item_data = self.parse_item_page(item_html, link)
                    all_data.append(item_data)
                    logging.info(f"Scraped: {item_data.get('title', 'Unknown')}")
            
            # Get next page
            current_url = self.get_next_page_url(soup)
            page_count += 1
            time.sleep(self.delay)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        logging.info(f"Scraping complete. Total items: {len(df)}")
        return df
    
    def export_to_csv(self, df, filename='scraped_data.csv'):
        """Export DataFrame to CSV with proper formatting"""
        df.to_csv(filename, index=False, encoding='utf-8')
        logging.info(f"Data exported to {filename}")
        
    def export_to_json(self, df, filename='scraped_data.json'):
        """Export DataFrame to JSON"""
        df.to_json(filename, orient='records', indent=2)
        logging.info(f"Data exported to {filename}")


# Example usage
if __name__ == "__main__":
    # Example configuration - replace with actual website
    BASE_URL = "https://example-ecommerce-site.com"
    START_URL = f"{BASE_URL}/products?page=1"
    
    # Initialize scraper
    scraper = MultiLevelScraper(BASE_URL, delay=2)
    
    # Scrape data
    data = scraper.scrape(START_URL, max_pages=3)
    
    # Export results
    scraper.export_to_csv(data, 'products_data.csv')
    scraper.export_to_json(data, 'products_data.json')
    
    # Display summary statistics
    print("\n=== Scraping Summary ===")
    print(f"Total items scraped: {len(data)}")
    print(f"\nSample data:")
    print(data.head())
    print(f"\nData types:")
    print(data.dtypes)
    print(f"\nMissing values:")
    print(data.isnull().sum())