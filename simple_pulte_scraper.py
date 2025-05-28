#!/usr/bin/env python3
"""
Simple PulteGroup Job Scraper
Basic version using only requests and BeautifulSoup
"""

import requests
import csv
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import argparse
from urllib.parse import urljoin, urlparse
from pathlib import Path

class SimplePulteJobScraper:
    def __init__(self, base_url: str = "https://pultegroup.wd1.myworkdayjobs.com/PGI", 
                 delay: float = 2.0, max_retries: int = 3):
        """
        Initialize the simple PulteGroup job scraper.
        """
        self.base_url = base_url
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Set up headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        self.jobs_data = []
        
    def make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                print(f"  Requesting: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                print(f"  ❌ Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                else:
                    print(f"  ❌ All retry attempts failed for URL: {url}")
                    
        return None
    
    def parse_jobs_from_html(self, html_content: str, page_url: str) -> List[Dict]:
        """Parse jobs from HTML content."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("❌ BeautifulSoup not installed. Install with: pip install beautifulsoup4")
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            jobs = []
            
            print(f"  📄 Parsing HTML content ({len(html_content)} characters)")
            
            # Look for job-related links and elements
            job_links = []
            
            # Method 1: Find links with 'job' in href
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if any(keyword in href.lower() for keyword in ['job', 'position', 'career']):
                    job_links.append(link)
            
            print(f"  🔗 Found {len(job_links)} potential job links")
            
            # Method 2: Look for structured job data
            job_containers = soup.find_all(['div', 'li', 'article'], class_=re.compile(r'job|posting|position', re.I))
            print(f"  📦 Found {len(job_containers)} job containers")
            
            # Method 3: Look for data attributes
            data_elements = soup.find_all(attrs={'data-automation-id': True})
            job_data_elements = [elem for elem in data_elements if 'job' in elem.get('data-automation-id', '').lower()]
            print(f"  🏷️  Found {len(job_data_elements)} elements with job data attributes")
            
            # Process all potential job elements
            all_elements = list(set(job_links + job_containers + job_data_elements))
            print(f"  🔍 Processing {len(all_elements)} total elements")
            
            for element in all_elements:
                job_data = self.extract_job_from_element(element, page_url)
                if job_data and job_data.get('title'):
                    jobs.append(job_data)
            
            # Remove duplicates based on title and URL
            unique_jobs = []
            seen = set()
            for job in jobs:
                key = (job.get('title', ''), job.get('url', ''))
                if key not in seen:
                    seen.add(key)
                    unique_jobs.append(job)
            
            print(f"  ✅ Extracted {len(unique_jobs)} unique jobs")
            return unique_jobs
            
        except Exception as e:
            print(f"  ❌ Error parsing HTML: {e}")
            return []
    
    def extract_job_from_element(self, element, page_url: str) -> Optional[Dict]:
        """Extract job data from a BeautifulSoup element."""
        try:
            job_data = {
                'scraped_at': datetime.now().isoformat(),
                'company': 'PulteGroup',
                'job_id': '',
                'title': '',
                'location': '',
                'posting_date': '',
                'url': ''
            }
            
            # Extract title - try multiple methods
            title_text = ''
            
            # Method 1: Direct text content
            if element.name == 'a' and element.get_text(strip=True):
                title_text = element.get_text(strip=True)
            
            # Method 2: Look for title in child elements
            if not title_text:
                title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.job-title', '[data-automation-id*="title"]']
                for selector in title_selectors:
                    title_elem = element.select_one(selector)
                    if title_elem and title_elem.get_text(strip=True):
                        title_text = title_elem.get_text(strip=True)
                        break
            
            # Method 3: Use element text if it looks like a job title
            if not title_text:
                text = element.get_text(strip=True)
                if text and len(text) < 200 and any(word in text.lower() for word in ['engineer', 'manager', 'analyst', 'specialist', 'coordinator', 'director', 'associate']):
                    title_text = text
            
            if title_text:
                job_data['title'] = title_text[:200]  # Limit length
            
            # Extract location
            location_selectors = ['.location', '.job-location', '[data-automation-id*="location"]']
            for selector in location_selectors:
                location_elem = element.select_one(selector)
                if location_elem and location_elem.get_text(strip=True):
                    job_data['location'] = location_elem.get_text(strip=True)
                    break
            
            # Extract date
            date_selectors = ['.date', '.job-date', '[data-automation-id*="date"]']
            for selector in date_selectors:
                date_elem = element.select_one(selector)
                if date_elem and date_elem.get_text(strip=True):
                    job_data['posting_date'] = date_elem.get_text(strip=True)
                    break
            
            # Extract URL
            if element.name == 'a' and element.get('href'):
                href = element['href']
                if href.startswith('/'):
                    job_data['url'] = urljoin(self.base_url, href)
                elif href.startswith('http'):
                    job_data['url'] = href
            else:
                # Look for link in child elements
                link = element.find('a', href=True)
                if link:
                    href = link['href']
                    if href.startswith('/'):
                        job_data['url'] = urljoin(self.base_url, href)
                    elif href.startswith('http'):
                        job_data['url'] = href
            
            # Extract job ID from URL or attributes
            if job_data['url']:
                # Try to extract ID from URL
                url_parts = job_data['url'].split('/')
                for part in reversed(url_parts):
                    if part and not part.startswith('http') and len(part) > 3:
                        job_data['job_id'] = part
                        break
            
            # Try to get ID from element attributes
            if not job_data['job_id']:
                for attr in ['data-job-id', 'id', 'data-automation-id']:
                    attr_value = element.get(attr)
                    if attr_value:
                        job_data['job_id'] = attr_value
                        break
            
            # Only return if we have at least a title
            if job_data.get('title') and len(job_data['title'].strip()) > 3:
                return job_data
                
        except Exception as e:
            print(f"    ⚠️ Error extracting job data: {e}")
            
        return None
    
    def find_pagination_urls(self, html_content: str, current_url: str) -> List[str]:
        """Find pagination URLs from HTML content."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            pagination_urls = []
            
            # Look for pagination links
            pagination_selectors = [
                'a[href*="page"]',
                'a[href*="offset"]',
                'a[aria-label*="Next"]',
                'a[title*="Next"]',
                '.pagination a',
                '.pager a',
                '[data-automation-id*="next"] a',
                '[data-automation-id*="page"] a'
            ]
            
            for selector in pagination_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        if href.startswith('/'):
                            full_url = urljoin(self.base_url, href)
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue
                        
                        if full_url != current_url and full_url not in pagination_urls:
                            pagination_urls.append(full_url)
            
            return pagination_urls[:5]  # Limit to 5 pages to avoid infinite loops
            
        except Exception as e:
            print(f"  ❌ Error finding pagination URLs: {e}")
            return []
    
    def scrape_jobs(self) -> List[Dict]:
        """Main method to scrape jobs."""
        print("🚀 Starting simple job scraping...")
        print(f"📍 Target URL: {self.base_url}")
        
        all_jobs = []
        visited_urls = set()
        urls_to_visit = [self.base_url]
        
        while urls_to_visit and len(visited_urls) < 10:  # Limit to 10 pages
            current_url = urls_to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
                
            visited_urls.add(current_url)
            print(f"\n📄 Scraping page {len(visited_urls)}: {current_url}")
            
            # Get page content
            response = self.make_request(current_url)
            if not response:
                print(f"  ❌ Failed to get page content")
                continue
            
            # Parse jobs from this page
            page_jobs = self.parse_jobs_from_html(response.text, current_url)
            
            if page_jobs:
                all_jobs.extend(page_jobs)
                print(f"  ✅ Found {len(page_jobs)} jobs on this page")
                
                # Look for pagination links
                pagination_urls = self.find_pagination_urls(response.text, current_url)
                for url in pagination_urls:
                    if url not in visited_urls and url not in urls_to_visit:
                        urls_to_visit.append(url)
                        print(f"  🔗 Added pagination URL: {url}")
            else:
                print(f"  ⚠️ No jobs found on this page")
            
            # Be respectful with delays
            time.sleep(self.delay)
        
        print(f"\n📊 Total jobs found: {len(all_jobs)}")
        return all_jobs
    
    def save_to_csv(self, jobs: List[Dict], filename: str = None) -> str:
        """Save jobs data to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pulte_jobs_simple_{timestamp}.csv"
        
        # Create output directory if it doesn't exist
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename
        
        if not jobs:
            print("⚠️ No jobs to save")
            return str(filepath)
        
        fieldnames = ['job_id', 'title', 'location', 'posting_date', 'url', 'company', 'scraped_at']
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for job in jobs:
                    # Ensure all required fields exist and clean data
                    row = {}
                    for field in fieldnames:
                        value = job.get(field, '')
                        # Clean up the value
                        if isinstance(value, str):
                            value = value.strip().replace('\n', ' ').replace('\r', '')
                        row[field] = value
                    writer.writerow(row)
            
            print(f"💾 Saved {len(jobs)} jobs to {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Simple PulteGroup job scraper')
    parser.add_argument('--url', default='https://pultegroup.wd1.myworkdayjobs.com/PGI',
                       help='Base URL for job site')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between requests in seconds')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum number of retries for failed requests')
    
    args = parser.parse_args()
    
    scraper = SimplePulteJobScraper(
        base_url=args.url,
        delay=args.delay,
        max_retries=args.max_retries
    )
    
    try:
        jobs = scraper.scrape_jobs()
        
        if jobs:
            print(f"\n✅ Successfully scraped {len(jobs)} jobs!")
            
            # Save to CSV
            csv_filename = scraper.save_to_csv(jobs, args.output)
            print(f"📄 Data saved to: {csv_filename}")
            
            # Print summary
            print(f"\n📊 Summary:")
            print(f"   Total jobs: {len(jobs)}")
            
            # Show sample data
            if jobs:
                print(f"   Sample jobs:")
                for i, job in enumerate(jobs[:3]):
                    print(f"     {i+1}. {job.get('title', 'No title')}")
                    if job.get('location'):
                        print(f"        📍 {job['location']}")
                    if job.get('url'):
                        print(f"        🔗 {job['url']}")
            
        else:
            print("❌ No jobs were scraped.")
            print("💡 This might be because:")
            print("   - The website uses heavy JavaScript (try the Selenium version)")
            print("   - The website has anti-bot protection")
            print("   - The page structure has changed")
            print("   - Network connectivity issues")
            
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error during scraping: {e}")

if __name__ == "__main__":
    main() 