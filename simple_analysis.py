#!/usr/bin/env python3
"""
Simple analysis of scraped job data without pandas
"""

import csv
import glob
import os
from pathlib import Path
from collections import Counter

def analyze_job_data():
    """Analyze the most recent job data file."""
    
    # Find the most recent CSV file in output directory
    output_dir = Path('output')
    if not output_dir.exists():
        print("❌ No output directory found")
        return
    
    csv_files = list(output_dir.glob('*.csv'))
    if not csv_files:
        print("❌ No CSV files found in output directory")
        return
    
    # Get the most recent file
    latest_file = max(csv_files, key=os.path.getctime)
    print(f"📄 Analyzing: {latest_file}")
    
    try:
        # Read the CSV file
        jobs = []
        with open(latest_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                jobs.append(row)
        
        print(f"\n📊 Job Data Analysis")
        print("=" * 50)
        
        # Basic statistics
        total_jobs = len(jobs)
        print(f"📈 Total jobs scraped: {total_jobs}")
        
        if total_jobs == 0:
            print("❌ No job data found")
            return
        
        print(f"📅 Data scraped on: {jobs[0]['scraped_at'][:10] if jobs[0]['scraped_at'] else 'Unknown'}")
        
        # Company information
        companies = [job['company'] for job in jobs if job['company']]
        company_counts = Counter(companies)
        print(f"🏢 Companies: {', '.join(company_counts.keys())}")
        
        # Location analysis
        locations = [job['location'] for job in jobs if job['location']]
        location_counts = Counter(locations)
        unique_locations = len(location_counts)
        print(f"📍 Unique locations: {unique_locations}")
        
        if unique_locations > 0:
            print(f"\n🔝 Top 10 locations:")
            for location, count in location_counts.most_common(10):
                print(f"   {location}: {count} jobs")
        
        # Job title analysis
        titles = [job['title'] for job in jobs if job['title']]
        print(f"\n💼 Sample job titles:")
        for i, title in enumerate(titles[:10]):
            print(f"   {i+1}. {title}")
        
        # URL analysis
        urls_with_data = [job for job in jobs if job['url']]
        print(f"\n🔗 Jobs with URLs: {len(urls_with_data)}/{total_jobs} ({len(urls_with_data)/total_jobs*100:.1f}%)")
        
        # Posting date analysis
        dates_with_data = [job['posting_date'] for job in jobs if job['posting_date']]
        date_counts = Counter(dates_with_data)
        print(f"📅 Jobs with posting dates: {len(dates_with_data)}/{total_jobs} ({len(dates_with_data)/total_jobs*100:.1f}%)")
        
        if len(dates_with_data) > 0:
            print(f"📆 Posting date distribution:")
            for date, count in date_counts.most_common(5):
                print(f"   {date}: {count} jobs")
        
        # Data completeness
        print(f"\n📋 Data completeness:")
        fieldnames = ['job_id', 'title', 'location', 'posting_date', 'url', 'company', 'scraped_at']
        for field in fieldnames:
            non_empty_count = sum(1 for job in jobs if job.get(field, '').strip())
            percentage = (non_empty_count / total_jobs) * 100
            print(f"   {field}: {non_empty_count}/{total_jobs} ({percentage:.1f}%)")
        
        # Job type analysis (basic keyword detection)
        print(f"\n🏷️ Job categories (based on titles):")
        categories = {
            'Sales': ['sales', 'consultant'],
            'Management': ['manager', 'director', 'supervisor'],
            'Engineering': ['engineer', 'technical'],
            'Finance': ['finance', 'accounting', 'mortgage'],
            'Construction': ['construction', 'superintendent', 'foreman'],
            'Marketing': ['marketing', 'coordinator'],
            'Administrative': ['administrator', 'assistant', 'clerk']
        }
        
        category_counts = {}
        for category, keywords in categories.items():
            count = 0
            for job in jobs:
                title = job.get('title', '').lower()
                if any(keyword in title for keyword in keywords):
                    count += 1
            if count > 0:
                category_counts[category] = count
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count} jobs")
        
        print(f"\n✅ Analysis complete!")
        print(f"📁 Full data available in: {latest_file}")
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")

if __name__ == "__main__":
    analyze_job_data() 