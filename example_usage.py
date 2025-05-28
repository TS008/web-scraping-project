#!/usr/bin/env python3
"""
Example usage of the PulteGroup job scraper
"""

from enhanced_pulte_scraper import EnhancedPulteJobScraper
import pandas as pd

def main():
    print("🚀 PulteGroup Job Scraper Example")
    print("=" * 40)
    
    # Initialize the scraper
    scraper = EnhancedPulteJobScraper(
        base_url="https://pultegroup.wd1.myworkdayjobs.com/PGI",
        delay=1.5,  # Be respectful with delays
        max_retries=3,
        headless=True  # Run in background
    )
    
    try:
        # Scrape jobs
        print("📊 Starting job scraping...")
        jobs = scraper.scrape_jobs()
        
        if jobs:
            print(f"✅ Found {len(jobs)} jobs!")
            
            # Save to CSV
            csv_file = scraper.save_to_csv(jobs, "pulte_jobs_example.csv")
            print(f"💾 Saved to: {csv_file}")
            
            # Save to JSON
            json_file = scraper.save_to_json(jobs, "pulte_jobs_example.json")
            print(f"💾 Saved to: {json_file}")
            
            # Display some statistics using pandas
            try:
                df = pd.DataFrame(jobs)
                print(f"\n📈 Job Statistics:")
                print(f"   Total jobs: {len(df)}")
                
                if 'location' in df.columns:
                    location_counts = df['location'].value_counts().head(5)
                    print(f"   Top 5 locations:")
                    for location, count in location_counts.items():
                        print(f"     {location}: {count} jobs")
                
                if 'title' in df.columns:
                    print(f"   Sample job titles:")
                    for title in df['title'].head(3):
                        print(f"     • {title}")
                        
            except ImportError:
                print("   (Install pandas for detailed statistics: pip install pandas)")
                
        else:
            print("❌ No jobs found. Check the website URL and try again.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 