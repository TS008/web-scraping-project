#!/usr/bin/env python3
"""
Enhanced PulteGroup Workday Job Scraper
Advanced scraper with automatic webdriver management, better error handling,
and multiple scraping strategies.
"""

import requests
import json
import csv
import time
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import argparse
from urllib.parse import urljoin, urlparse, parse_qs
import sys
import os
from pathlib import Path

class EnhancedPulteJobScraper:
    def __init__(self, base_url: str = "https://pultegroup.wd1.myworkdayjobs.com/PGI", 
                 delay: float = 1.0, max_retries: int = 3, headless: bool = True):
        """
        Initialize the enhanced PulteGroup job scraper.
        
        Args:
            base_url: Base URL for the job site
            delay: Delay between requests in seconds
            max_retries: Maximum number of retries for failed requests
            headless: Whether to run browser in headless mode
        """
        self.base_url = base_url
        self.delay = delay
        self.max_retries = max_retries
        self.headless = headless
        self.session = requests.Session()
        
        # Set up headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Set up logging
        self.setup_logging()
        self.jobs_data = []
        self.driver = None
        
    def setup_logging(self):
        """Set up logging configuration."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'logs/pulte_scraper_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_selenium_driver(self):
        """Set up Selenium WebDriver with automatic management."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Add various options for better compatibility
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Use webdriver-manager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Selenium WebDriver initialized successfully")
            return True
            
        except ImportError:
            self.logger.error("Selenium or webdriver-manager not installed. Install with: pip install selenium webdriver-manager")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make a request with retry logic and error handling."""
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=30, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, timeout=30, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                else:
                    self.logger.error(f"All retry attempts failed for URL: {url}")
                    
        return None
    
    def discover_workday_endpoints(self) -> List[str]:
        """Discover potential Workday API endpoints."""
        endpoints = []
        
        # Common Workday patterns
        base_patterns = [
            f"{self.base_url}/jobs",
            f"{self.base_url}/jobSearch",
            f"{self.base_url}/wday/cxs/pultegroup/PGI/jobs",
            f"https://pultegroup.wd1.myworkdayjobs.com/wday/cxs/pultegroup/PGI/jobs",
        ]
        
        # Try to extract from the main page
        try:
            response = self.make_request(self.base_url)
            if response:
                content = response.text
                
                # Look for API endpoints in JavaScript
                api_patterns = [
                    r'["\']([^"\']*(?:jobs|search)[^"\']*)["\']',
                    r'endpoint["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'url["\']?\s*:\s*["\']([^"\']*jobs[^"\']*)["\']'
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if match.startswith('/'):
                            full_url = urljoin(self.base_url, match)
                            endpoints.append(full_url)
                        elif match.startswith('http'):
                            endpoints.append(match)
                            
        except Exception as e:
            self.logger.warning(f"Error analyzing main page: {e}")
        
        # Combine with base patterns
        all_endpoints = list(set(base_patterns + endpoints))
        return all_endpoints
    
    def test_api_endpoint(self, endpoint: str) -> Tuple[bool, Optional[Dict]]:
        """Test if an API endpoint returns job data."""
        try:
            # Try different parameter combinations
            param_sets = [
                {'offset': 0, 'limit': 20},
                {'from': 0, 'size': 20},
                {'page': 1, 'pageSize': 20},
                {}  # No parameters
            ]
            
            for params in param_sets:
                response = self.make_request(endpoint, params=params)
                if response and response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Check if response contains job data
                        if self.is_job_data(data):
                            self.logger.info(f"Working API endpoint found: {endpoint}")
                            return True, data
                            
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.debug(f"Error testing endpoint {endpoint}: {e}")
            
        return False, None
    
    def is_job_data(self, data) -> bool:
        """Check if the data structure contains job information."""
        if isinstance(data, list) and data:
            # Check if list contains job-like objects
            first_item = data[0]
            if isinstance(first_item, dict):
                job_fields = ['title', 'location', 'id', 'jobTitle', 'position']
                return any(field in first_item for field in job_fields)
                
        elif isinstance(data, dict):
            # Check for common job data structures
            job_containers = ['jobPostings', 'jobs', 'data', 'results', 'items']
            for container in job_containers:
                if container in data and isinstance(data[container], list):
                    return True
                    
            # Check if the dict itself is a job
            job_fields = ['title', 'location', 'id', 'jobTitle', 'position']
            return any(field in data for field in job_fields)
            
        return False
    
    def scrape_with_api(self) -> List[Dict]:
        """Scrape jobs using API endpoints."""
        self.logger.info("Attempting API-based scraping...")
        
        endpoints = self.discover_workday_endpoints()
        
        for endpoint in endpoints:
            self.logger.info(f"Testing endpoint: {endpoint}")
            is_working, sample_data = self.test_api_endpoint(endpoint)
            
            if is_working:
                return self.paginate_api_endpoint(endpoint, sample_data)
        
        self.logger.warning("No working API endpoints found")
        return []
    
    def paginate_api_endpoint(self, endpoint: str, sample_data: Dict) -> List[Dict]:
        """Paginate through an API endpoint to get all jobs."""
        all_jobs = []
        offset = 0
        limit = 20
        page = 1
        
        while True:
            self.logger.info(f"Fetching page {page} (offset: {offset})")
            
            # Try different pagination parameters
            param_sets = [
                {'offset': offset, 'limit': limit},
                {'from': offset, 'size': limit},
                {'page': page, 'pageSize': limit},
                {'start': offset, 'count': limit}
            ]
            
            jobs_found = False
            
            for params in param_sets:
                response = self.make_request(endpoint, params=params)
                if response and response.status_code == 200:
                    try:
                        data = response.json()
                        jobs = self.extract_jobs_from_response(data)
                        
                        if jobs:
                            all_jobs.extend(jobs)
                            self.logger.info(f"Found {len(jobs)} jobs on page {page}")
                            jobs_found = True
                            
                            # Check if we should continue
                            if len(jobs) < limit:
                                self.logger.info("Received fewer jobs than limit, assuming last page")
                                return all_jobs
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            if not jobs_found:
                self.logger.info("No more jobs found, pagination complete")
                break
                
            offset += limit
            page += 1
            time.sleep(self.delay)
        
        return all_jobs
    
    def extract_jobs_from_response(self, data) -> List[Dict]:
        """Extract job data from API response."""
        jobs = []
        
        if isinstance(data, list):
            jobs = data
        elif isinstance(data, dict):
            # Try different container keys
            containers = ['jobPostings', 'jobs', 'data', 'results', 'items']
            for container in containers:
                if container in data and isinstance(data[container], list):
                    jobs = data[container]
                    break
        
        processed_jobs = []
        for job in jobs:
            processed_job = self.process_job_data(job)
            if processed_job:
                processed_jobs.append(processed_job)
        
        return processed_jobs
    
    def scrape_with_selenium(self) -> List[Dict]:
        """Scrape jobs using Selenium for JavaScript-heavy sites."""
        if not self.setup_selenium_driver():
            return []
        
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException, NoSuchElementException
            
            self.logger.info("Starting Selenium-based scraping...")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            time.sleep(3)
            
            all_jobs = []
            page = 1
            
            while True:
                self.logger.info(f"Scraping page {page} with Selenium...")
                
                try:
                    # Wait for job listings to load with multiple possible selectors
                    job_selectors = [
                        "[data-automation-id='jobPostingItem']",
                        "[data-automation-id='job-posting']",
                        ".job-posting",
                        ".job-item",
                        ".WDKF_JobPosting",
                        "[role='listitem']",
                        ".css-1q2dra3",  # Common Workday class
                        "[data-uxi-element-id*='job']"
                    ]
                    
                    job_elements = []
                    for selector in job_selectors:
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                job_elements = elements
                                self.logger.info(f"Found job elements using selector: {selector}")
                                break
                        except TimeoutException:
                            continue
                    
                    if not job_elements:
                        # Try to find any clickable job links
                        link_selectors = [
                            "a[href*='job']",
                            "a[data-automation-id*='job']",
                            ".job-title a",
                            "[data-automation-id='jobPostingTitle'] a"
                        ]
                        
                        for selector in link_selectors:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                job_elements = elements
                                self.logger.info(f"Found job links using selector: {selector}")
                                break
                    
                    if not job_elements:
                        self.logger.warning("No job elements found on page")
                        break
                    
                    page_jobs = []
                    for i, element in enumerate(job_elements):
                        try:
                            job_data = self.extract_job_data_selenium(element)
                            if job_data:
                                page_jobs.append(job_data)
                        except Exception as e:
                            self.logger.warning(f"Error extracting job {i+1}: {e}")
                            continue
                    
                    if not page_jobs:
                        self.logger.info("No valid jobs found on this page")
                        break
                    
                    all_jobs.extend(page_jobs)
                    self.logger.info(f"Found {len(page_jobs)} jobs on page {page}")
                    
                    # Try to navigate to next page
                    if not self.go_to_next_page():
                        self.logger.info("No more pages available")
                        break
                    
                    page += 1
                    time.sleep(self.delay)
                    
                except Exception as e:
                    self.logger.error(f"Error during page {page} scraping: {e}")
                    break
            
            return all_jobs
            
        except Exception as e:
            self.logger.error(f"Selenium scraping failed: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    
    def go_to_next_page(self) -> bool:
        """Try to navigate to the next page."""
        try:
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import NoSuchElementException
            
            # Multiple selectors for next page button
            next_selectors = [
                "[data-automation-id='nextPage']",
                "[data-automation-id='next-page']",
                ".next-page",
                "[aria-label*='Next']",
                "button[title*='Next']",
                ".pagination-next",
                "[data-uxi-element-id*='next']",
                "button:contains('Next')",
                "a:contains('Next')"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled() and next_button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    continue
            
            # Try pagination by page numbers
            try:
                current_page = self.driver.find_element(By.CSS_SELECTOR, "[aria-current='page'], .current-page, .active")
                if current_page:
                    # Look for next page number
                    next_page_num = int(current_page.text) + 1
                    next_page_link = self.driver.find_element(By.XPATH, f"//a[text()='{next_page_num}']")
                    if next_page_link:
                        self.driver.execute_script("arguments[0].click();", next_page_link)
                        time.sleep(2)
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error navigating to next page: {e}")
            return False
    
    def extract_job_data_selenium(self, element) -> Optional[Dict]:
        """Extract job data from a Selenium WebElement."""
        try:
            from selenium.webdriver.common.by import By
            
            job_data = {
                'scraped_at': datetime.now().isoformat(),
                'company': 'PulteGroup'
            }
            
            # Extract job title
            title_selectors = [
                "[data-automation-id='jobPostingTitle']",
                "[data-automation-id='job-title']",
                ".job-title",
                "h3",
                "h2",
                ".title",
                "a[data-automation-id*='title']"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    job_data['title'] = title_elem.text.strip()
                    break
                except:
                    continue
            
            # If no title found, try getting it from link text
            if not job_data.get('title'):
                try:
                    link = element.find_element(By.TAG_NAME, "a")
                    if link.text.strip():
                        job_data['title'] = link.text.strip()
                except:
                    pass
            
            # Extract location
            location_selectors = [
                "[data-automation-id='jobPostingLocation']",
                "[data-automation-id='location']",
                ".job-location",
                ".location",
                "[data-uxi-element-id*='location']"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = element.find_element(By.CSS_SELECTOR, selector)
                    job_data['location'] = location_elem.text.strip()
                    break
                except:
                    continue
            
            # Extract posting date
            date_selectors = [
                "[data-automation-id='jobPostingDate']",
                "[data-automation-id='date']",
                ".job-date",
                ".posting-date",
                ".date",
                "[data-uxi-element-id*='date']"
            ]
            
            for selector in date_selectors:
                try:
                    date_elem = element.find_element(By.CSS_SELECTOR, selector)
                    job_data['posting_date'] = date_elem.text.strip()
                    break
                except:
                    continue
            
            # Extract job URL
            try:
                link = element.find_element(By.TAG_NAME, "a")
                href = link.get_attribute('href')
                if href:
                    job_data['url'] = href
            except:
                pass
            
            # Extract job ID from URL or element attributes
            if job_data.get('url'):
                # Try to extract ID from URL
                url_parts = job_data['url'].split('/')
                for part in reversed(url_parts):
                    if part and not part.startswith('http'):
                        job_data['job_id'] = part
                        break
            
            # Try to get ID from element attributes
            if not job_data.get('job_id'):
                for attr in ['data-job-id', 'id', 'data-automation-id']:
                    try:
                        attr_value = element.get_attribute(attr)
                        if attr_value:
                            job_data['job_id'] = attr_value
                            break
                    except:
                        continue
            
            # Only return if we have at least a title
            if job_data.get('title'):
                return job_data
            else:
                self.logger.debug("Job element found but no title extracted")
                
        except Exception as e:
            self.logger.warning(f"Error extracting job data from element: {e}")
            
        return None
    
    def process_job_data(self, job: Dict) -> Optional[Dict]:
        """Process and standardize job data from API response."""
        try:
            processed = {
                'job_id': '',
                'title': '',
                'location': '',
                'posting_date': '',
                'url': '',
                'company': 'PulteGroup',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract job ID
            id_fields = ['id', 'jobId', 'postingId', 'requisitionId']
            for field in id_fields:
                if job.get(field):
                    processed['job_id'] = str(job[field])
                    break
            
            # Extract title
            title_fields = ['title', 'jobTitle', 'positionTitle', 'name']
            for field in title_fields:
                if job.get(field):
                    processed['title'] = job[field]
                    break
            
            # Extract location
            if job.get('locationsText'):
                processed['location'] = job['locationsText']
            elif job.get('location'):
                if isinstance(job['location'], dict):
                    processed['location'] = job['location'].get('name', '')
                else:
                    processed['location'] = str(job['location'])
            elif job.get('bulletFields'):
                for field in job['bulletFields']:
                    if 'location' in field.get('type', '').lower():
                        processed['location'] = field.get('value', '')
                        break
            
            # Extract posting date
            date_fields = ['postedOn', 'postingDate', 'datePosted', 'createdDate']
            for field in date_fields:
                if job.get(field):
                    processed['posting_date'] = job[field]
                    break
            
            # Build job URL
            if job.get('externalPath'):
                processed['url'] = urljoin(self.base_url, job['externalPath'])
            elif job.get('url'):
                processed['url'] = job['url']
            elif processed['job_id']:
                processed['url'] = f"{self.base_url}/{processed['job_id']}"
            
            return processed
            
        except Exception as e:
            self.logger.warning(f"Error processing job data: {e}")
            return None
    
    def scrape_jobs(self) -> List[Dict]:
        """Main method to scrape jobs with multiple strategies."""
        self.logger.info("Starting comprehensive job scraping...")
        
        # Strategy 1: Try API approach first
        jobs = self.scrape_with_api()
        
        if jobs:
            self.logger.info(f"API scraping successful: {len(jobs)} jobs found")
            return jobs
        
        # Strategy 2: Fall back to Selenium
        self.logger.info("API scraping failed, trying Selenium approach...")
        jobs = self.scrape_with_selenium()
        
        if jobs:
            self.logger.info(f"Selenium scraping successful: {len(jobs)} jobs found")
            return jobs
        
        self.logger.error("All scraping strategies failed")
        return []
    
    def save_to_csv(self, jobs: List[Dict], filename: str = None) -> str:
        """Save jobs data to CSV file with enhanced formatting."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pulte_jobs_{timestamp}.csv"
        
        # Create output directory if it doesn't exist
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename
        
        if not jobs:
            self.logger.warning("No jobs to save")
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
            
            self.logger.info(f"Saved {len(jobs)} jobs to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
            raise
    
    def save_to_json(self, jobs: List[Dict], filename: str = None) -> str:
        """Save jobs data to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pulte_jobs_{timestamp}.json"
        
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(jobs, jsonfile, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(jobs)} jobs to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced scraper for PulteGroup Workday job listings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_pulte_scraper.py
  python enhanced_pulte_scraper.py --output my_jobs.csv --verbose
  python enhanced_pulte_scraper.py --delay 2.0 --no-headless
        """
    )
    
    parser.add_argument('--url', default='https://pultegroup.wd1.myworkdayjobs.com/PGI',
                       help='Base URL for job site (default: %(default)s)')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--json-output', help='Output JSON filename')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: %(default)s)')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum number of retries for failed requests (default: %(default)s)')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run browser in non-headless mode (visible)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    scraper = EnhancedPulteJobScraper(
        base_url=args.url,
        delay=args.delay,
        max_retries=args.max_retries,
        headless=not args.no_headless
    )
    
    try:
        print("🚀 Starting PulteGroup job scraping...")
        print(f"📍 Target URL: {args.url}")
        print(f"⏱️  Request delay: {args.delay}s")
        print(f"🔄 Max retries: {args.max_retries}")
        print(f"👁️  Headless mode: {not args.no_headless}")
        print("-" * 50)
        
        jobs = scraper.scrape_jobs()
        
        if jobs:
            print(f"\n✅ Successfully scraped {len(jobs)} jobs!")
            
            # Save to CSV
            csv_filename = scraper.save_to_csv(jobs, args.output)
            print(f"📄 CSV data saved to: {csv_filename}")
            
            # Save to JSON if requested
            if args.json_output:
                json_filename = scraper.save_to_json(jobs, args.json_output)
                print(f"📄 JSON data saved to: {json_filename}")
            
            # Print summary statistics
            print(f"\n📊 Summary:")
            print(f"   Total jobs: {len(jobs)}")
            
            if jobs:
                # Location statistics
                locations = [job.get('location', 'Unknown') for job in jobs if job.get('location')]
                unique_locations = set(locations)
                print(f"   Unique locations: {len(unique_locations)}")
                if unique_locations:
                    print(f"   Sample locations: {', '.join(list(unique_locations)[:5])}")
                
                # Jobs with URLs
                jobs_with_urls = sum(1 for job in jobs if job.get('url'))
                print(f"   Jobs with URLs: {jobs_with_urls}")
                
                # Recent jobs (if posting dates available)
                recent_jobs = sum(1 for job in jobs if job.get('posting_date'))
                print(f"   Jobs with posting dates: {recent_jobs}")
            
        else:
            print("❌ No jobs were scraped.")
            print("💡 Troubleshooting tips:")
            print("   - Check if the website URL is correct")
            print("   - Try running with --verbose for more details")
            print("   - Try running with --no-headless to see browser interaction")
            print("   - Check your internet connection")
            
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 