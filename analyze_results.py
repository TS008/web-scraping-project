#!/usr/bin/env python3
"""
Analyze scraped job data
"""

import pandas as pd
import glob
import os
from pathlib import Path

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
        df = pd.read_csv(latest_file)
        
        print(f"\n📊 Job Data Analysis")
        print("=" * 50)
        
        # Basic statistics
        print(f"📈 Total jobs scraped: {len(df)}")
        print(f"📅 Data scraped on: {df['scraped_at'].iloc[0][:10] if len(df) > 0 else 'Unknown'}")
        
        # Company information
        if 'company' in df.columns:
            companies = df['company'].value_counts()
            print(f"🏢 Companies: {', '.join(companies.index.tolist())}")
        
        # Location analysis
        if 'location' in df.columns:
            locations = df['location'].dropna()
            unique_locations = locations.nunique()
            print(f"📍 Unique locations: {unique_locations}")
            
            if unique_locations > 0:
                top_locations = locations.value_counts().head(10)
                print(f"\n🔝 Top 10 locations:")
                for location, count in top_locations.items():
                    print(f"   {location}: {count} jobs")
        
        # Job title analysis
        if 'title' in df.columns:
            titles = df['title'].dropna()
            print(f"\n💼 Sample job titles:")
            for i, title in enumerate(titles.head(10)):
                print(f"   {i+1}. {title}")
        
        # URL analysis
        if 'url' in df.columns:
            urls_with_data = df['url'].dropna()
            print(f"\n🔗 Jobs with URLs: {len(urls_with_data)}/{len(df)} ({len(urls_with_data)/len(df)*100:.1f}%)")
        
        # Posting date analysis
        if 'posting_date' in df.columns:
            dates_with_data = df['posting_date'].dropna()
            print(f"📅 Jobs with posting dates: {len(dates_with_data)}/{len(df)} ({len(dates_with_data)/len(df)*100:.1f}%)")
            
            if len(dates_with_data) > 0:
                unique_dates = dates_with_data.value_counts()
                print(f"📆 Posting date distribution:")
                for date, count in unique_dates.head(5).items():
                    print(f"   {date}: {count} jobs")
        
        # Data completeness
        print(f"\n📋 Data completeness:")
        for column in df.columns:
            non_null_count = df[column].notna().sum()
            percentage = (non_null_count / len(df)) * 100
            print(f"   {column}: {non_null_count}/{len(df)} ({percentage:.1f}%)")
        
        print(f"\n✅ Analysis complete!")
        print(f"📁 Full data available in: {latest_file}")
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")

if __name__ == "__main__":
    analyze_job_data() 