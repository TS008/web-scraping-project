#!/usr/bin/env python3
"""
Simplified Workday API Job Scraper
Uses the known working payload format directly with improved job_id extraction
"""

import requests
import json
import csv
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import argparse
from urllib.parse import urljoin
from pathlib import Path

class SimpleWorkdayAPIJobScraper:
    def __init__(self, base_url: str = "https://pultegroup.wd1.myworkdayjobs.com/PGI", 
                 delay: float = 2.0, max_retries: int = 3):
        """
        Initialize the simple Workday API job scraper.
        """
        self.base_url = base_url
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Extract company and site info from URL
        self.company_info = self.parse_workday_url(base_url)
        
        # Set up headers for API calls
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': base_url,
            'Origin': f"https://{self.company_info['domain']}"
        })
        
    def parse_workday_url(self, url: str) -> Dict[str, str]:
        """Parse Workday URL to extract company and site information."""
        # Example: https://pultegroup.wd1.myworkdayjobs.com/PGI
        pattern = r'https://([^.]+)\.wd(\d+)\.myworkdayjobs\.com/([^/?]+)'
        match = re.match(pattern, url)
        
        if match:
            company = match.group(1)
            wd_version = match.group(2)
            site_id = match.group(3)
            domain = f"{company}.wd{wd_version}.myworkdayjobs.com"
            
            return {
                'company': company,
                'wd_version': wd_version,
                'site_id': site_id,
                'domain': domain
            }
        else:
            # Fallback parsing
            parts = url.replace('https://', '').split('/')
            domain = parts[0]
            site_id = parts[1] if len(parts) > 1 else 'careers'
            company = domain.split('.')[0]
            
            return {
                'company': company,
                'wd_version': '1',
                'site_id': site_id,
                'domain': domain
            }
    
    def build_api_url(self) -> str:
        """Build the correct API URL for this Workday site."""
        company = self.company_info['company']
        site_id = self.company_info['site_id']
        
        # Standard Workday API pattern
        api_url = f"https://{self.company_info['domain']}/wday/cxs/{company}/{site_id}/jobs"
        return api_url
    
    def make_api_request(self, url: str, payload: Dict) -> Optional[Dict]:
        """Make an API request with proper error handling."""
        for attempt in range(self.max_retries):
            try:
                print(f"  📡 API request (attempt {attempt + 1}): offset={payload.get('offset', 0)}")
                
                response = self.session.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data
                    except json.JSONDecodeError as e:
                        print(f"  ❌ JSON decode error: {e}")
                        
                else:
                    print(f"  ❌ HTTP {response.status_code}: {response.text[:200]}...")
                
            except requests.exceptions.RequestException as e:
                print(f"  ❌ Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                
            if attempt < self.max_retries - 1:
                wait_time = self.delay * (attempt + 1)
                time.sleep(wait_time)
        
        return None
    
    def scrape_jobs_api(self) -> List[Dict]:
        """Scrape jobs using the Workday API with known working payload."""
        print("🚀 Starting simple Workday API scraping...")
        
        api_url = self.build_api_url()
        print(f"🎯 API URL: {api_url}")
        
        # Use the known working payload format
        working_payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": ""
        }
        
        # Now paginate through all results
        all_jobs = []
        offset = 0
        limit = 20
        
        while True:
            print(f"\n📄 Fetching page with offset {offset}...")
            
            # Update payload for pagination
            current_payload = working_payload.copy()
            current_payload['offset'] = offset
            current_payload['limit'] = limit
            
            result = self.make_api_request(api_url, current_payload)
            
            if not result:
                print("❌ Failed to get results")
                break
            
            # Extract jobs from result
            jobs = self.extract_jobs_from_api_response(result)
            
            if not jobs:
                print("📭 No more jobs found")
                break
            
            all_jobs.extend(jobs)
            print(f"✅ Found {len(jobs)} jobs (total: {len(all_jobs)})")
            
            # Check if we should continue
            if len(jobs) < limit:
                print("📄 Received fewer jobs than limit, assuming last page")
                break
            
            offset += limit
            time.sleep(self.delay)
        
        return all_jobs
    
    def extract_jobs_from_api_response(self, data: Dict) -> List[Dict]:
        """Extract job data from API response."""
        jobs = []
        
        # Get job postings
        job_postings = data.get('jobPostings', [])
        
        if job_postings:
            print(f"📦 Found {len(job_postings)} jobs in response")
            
            for job_data in job_postings:
                processed_job = self.process_job_data(job_data)
                if processed_job:
                    jobs.append(processed_job)
        
        return jobs
    
    def process_job_data(self, job: Dict) -> Optional[Dict]:
        """Process and standardize job data from API response with improved job_id extraction."""
        try:
            processed = {
                'job_id': '',
                'title': '',
                'location': '',
                'posting_date': '',
                'url': '',
                'company': self.company_info['company'].title(),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract job ID - IMPROVED VERSION
            job_id = ''
            
            # Method 1: Extract from bulletFields (most reliable)
            if job.get('bulletFields') and isinstance(job['bulletFields'], list):
                for field in job['bulletFields']:
                    if isinstance(field, str) and field.strip():
                        # bulletFields often contains the job ID directly
                        job_id = field.strip()
                        break
            
            # Method 2: Extract from externalPath if bulletFields didn't work
            if not job_id and job.get('externalPath'):
                external_path = job['externalPath']
                # Extract ID from path like "/job/Location/Title_JR4032"
                if '_' in external_path:
                    # Split by underscore and take the last part
                    job_id = external_path.split('_')[-1]
                else:
                    # Fallback: use the last part of the path
                    path_parts = external_path.strip('/').split('/')
                    if path_parts:
                        job_id = path_parts[-1]
            
            # Method 3: Look for other ID fields
            if not job_id:
                id_fields = ['id', 'jobId', 'postingId', 'requisitionId', 'externalJobId']
                for field in id_fields:
                    if job.get(field):
                        job_id = str(job[field])
                        break
            
            processed['job_id'] = job_id
            
            # Extract title
            title_fields = ['title', 'jobTitle', 'positionTitle', 'name', 'jobName']
            for field in title_fields:
                if job.get(field):
                    processed['title'] = str(job[field]).strip()
                    break
            
            # Extract location
            location_text = ''
            if job.get('locationsText'):
                location_text = job['locationsText']
            elif job.get('location'):
                if isinstance(job['location'], dict):
                    location_text = job['location'].get('name', '')
                else:
                    location_text = str(job['location'])
            elif job.get('primaryLocation'):
                if isinstance(job['primaryLocation'], dict):
                    location_text = job['primaryLocation'].get('name', '')
                else:
                    location_text = str(job['primaryLocation'])
            
            processed['location'] = location_text.strip()
            
            # Extract posting date
            date_fields = ['postedOn', 'postingDate', 'datePosted', 'createdDate', 'publishedDate']
            for field in date_fields:
                if job.get(field):
                    processed['posting_date'] = str(job[field])
                    break
            
            # Build job URL
            if job.get('externalPath'):
                processed['url'] = urljoin(self.base_url, job['externalPath'])
            elif job.get('url'):
                processed['url'] = job['url']
            elif processed['job_id']:
                processed['url'] = f"{self.base_url}/job/{processed['job_id']}"
            
            # Only return if we have essential data
            if processed.get('title'):
                return processed
            
        except Exception as e:
            print(f"⚠️ Error processing job data: {e}")
            
        return None
    
    def save_to_csv(self, jobs: List[Dict], filename: str = None) -> str:
        """Save jobs data to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            company = self.company_info['company']
            filename = f"{company}_jobs_simple_{timestamp}.csv"
        
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
    parser = argparse.ArgumentParser(description='Simple Workday API job scraper with job_id extraction')
    parser.add_argument('--url', default='https://pultegroup.wd1.myworkdayjobs.com/PGI',
                       help='Workday job site URL')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--delay', type=float, default=3.0,
                       help='Delay between requests in seconds')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum number of retries for failed requests')
    
    args = parser.parse_args()
    
    scraper = SimpleWorkdayAPIJobScraper(
        base_url=args.url,
        delay=args.delay,
        max_retries=args.max_retries
    )
    
    try:
        print("🚀 Starting Simple Workday API job scraping...")
        print(f"📍 Target URL: {args.url}")
        print(f"🏢 Company: {scraper.company_info['company']}")
        print(f"🆔 Site ID: {scraper.company_info['site_id']}")
        print("-" * 50)
        
        jobs = scraper.scrape_jobs_api()
        
        if jobs:
            print(f"\n✅ Successfully scraped {len(jobs)} jobs!")
            
            # Save to CSV
            csv_filename = scraper.save_to_csv(jobs, args.output)
            print(f"📄 Data saved to: {csv_filename}")
            
            # Print summary with job_id statistics
            print(f"\n📊 Summary:")
            print(f"   Total jobs: {len(jobs)}")
            
            # Check job_id completeness
            jobs_with_id = sum(1 for job in jobs if job.get('job_id', '').strip())
            print(f"   Jobs with job_id: {jobs_with_id}/{len(jobs)} ({jobs_with_id/len(jobs)*100:.1f}%)")
            
            # Show sample data
            if jobs:
                print(f"   Sample jobs with IDs:")
                for i, job in enumerate(jobs[:3]):
                    job_id = job.get('job_id', 'No ID')
                    title = job.get('title', 'No title')
                    print(f"     {i+1}. [{job_id}] {title}")
            
        else:
            print("❌ No jobs were scraped.")
            
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error during scraping: {e}")

if __name__ == "__main__":
    main() 