# PulteGroup Job Scraper

A comprehensive Python script to scrape job listings from the PulteGroup Workday careers website with pagination support and CSV export functionality.

## 🚀 Features

- **Multiple Scraping Strategies**: Automatically tries API-based scraping first, falls back to Selenium for JavaScript-heavy sites
- **Pagination Support**: Automatically handles multiple pages of job listings
- **Robust Error Handling**: Retry logic, timeout handling, and graceful error recovery
- **Multiple Output Formats**: Save data to CSV and JSON formats
- **Automatic WebDriver Management**: Uses webdriver-manager for hassle-free Chrome driver setup
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Respectful Scraping**: Built-in delays and rate limiting to avoid overwhelming the server

## 📋 Requirements

- Python 3.7+
- Chrome browser (for Selenium fallback)
- Internet connection

## 🛠️ Installation

1. **Clone or download the scripts**:
   ```bash
   # If you have git
   git clone <repository-url>
   cd pulte-job-scraper
   
   # Or download the files directly
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install requests selenium beautifulsoup4 lxml pandas webdriver-manager
   ```

## 📖 Usage

### Basic Usage

**Simple scraping with default settings**:
```bash
python enhanced_pulte_scraper.py
```

**Specify output filename**:
```bash
python enhanced_pulte_scraper.py --output my_jobs.csv
```

**Enable verbose logging**:
```bash
python enhanced_pulte_scraper.py --verbose
```

**Run with visible browser (for debugging)**:
```bash
python enhanced_pulte_scraper.py --no-headless --verbose
```

### Advanced Usage

**Custom delay and retry settings**:
```bash
python enhanced_pulte_scraper.py --delay 2.0 --max-retries 5
```

**Save to both CSV and JSON**:
```bash
python enhanced_pulte_scraper.py --output jobs.csv --json-output jobs.json
```

**Scrape different Workday site**:
```bash
python enhanced_pulte_scraper.py --url "https://other-company.wd1.myworkdayjobs.com/careers"
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | Base URL for job site | `https://pultegroup.wd1.myworkdayjobs.com/PGI` |
| `--output`, `-o` | Output CSV filename | Auto-generated with timestamp |
| `--json-output` | Output JSON filename | None |
| `--delay` | Delay between requests (seconds) | `1.0` |
| `--max-retries` | Maximum retries for failed requests | `3` |
| `--no-headless` | Run browser in visible mode | False (headless) |
| `--verbose`, `-v` | Enable verbose logging | False |

## 🐍 Python API Usage

```python
from enhanced_pulte_scraper import EnhancedPulteJobScraper

# Initialize scraper
scraper = EnhancedPulteJobScraper(
    base_url="https://pultegroup.wd1.myworkdayjobs.com/PGI",
    delay=1.5,
    max_retries=3,
    headless=True
)

# Scrape jobs
jobs = scraper.scrape_jobs()

# Save results
if jobs:
    csv_file = scraper.save_to_csv(jobs, "my_jobs.csv")
    json_file = scraper.save_to_json(jobs, "my_jobs.json")
    print(f"Scraped {len(jobs)} jobs!")
```

## 📊 Output Format

The scraper extracts the following information for each job:

| Field | Description |
|-------|-------------|
| `job_id` | Unique job identifier |
| `title` | Job title |
| `location` | Job location |
| `posting_date` | Date when job was posted |
| `url` | Direct link to job posting |
| `company` | Company name (PulteGroup) |
| `scraped_at` | Timestamp when data was scraped |

### Sample CSV Output

```csv
job_id,title,location,posting_date,url,company,scraped_at
R0001234,Software Engineer,Atlanta GA,2024-01-15,https://pultegroup.wd1.myworkdayjobs.com/PGI/job/R0001234,PulteGroup,2024-01-20T10:30:00
R0001235,Project Manager,Phoenix AZ,2024-01-14,https://pultegroup.wd1.myworkdayjobs.com/PGI/job/R0001235,PulteGroup,2024-01-20T10:30:01
```

## 🔧 How It Works

The scraper uses a multi-strategy approach:

1. **API Discovery**: First attempts to find and use Workday's internal API endpoints
2. **Selenium Fallback**: If API approach fails, uses Selenium WebDriver to interact with the website
3. **Pagination Handling**: Automatically detects and navigates through multiple pages
4. **Data Extraction**: Extracts job information using multiple CSS selectors for robustness
5. **Data Processing**: Cleans and standardizes the extracted data
6. **Export**: Saves data to CSV and/or JSON formats

## 📁 File Structure

```
pulte-job-scraper/
├── enhanced_pulte_scraper.py    # Main enhanced scraper
├── pulte_job_scraper.py         # Basic scraper version
├── example_usage.py             # Usage example
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── logs/                        # Log files (created automatically)
└── output/                      # Output files (created automatically)
```

## 🐛 Troubleshooting

### Common Issues

**1. "No jobs were scraped"**
- Check if the website URL is correct
- Try running with `--verbose` for detailed logs
- Try running with `--no-headless` to see browser interaction
- Check your internet connection

**2. "Selenium or webdriver-manager not installed"**
```bash
pip install selenium webdriver-manager
```

**3. "ChromeDriver issues"**
- The script automatically downloads the correct ChromeDriver
- Make sure Chrome browser is installed
- Try updating Chrome to the latest version

**4. "Request failed" errors**
- Increase delay: `--delay 2.0`
- Increase retries: `--max-retries 5`
- Check if the website is accessible in your browser

**5. "Permission denied" when saving files**
- Make sure you have write permissions in the current directory
- Try running from a different directory

### Debug Mode

Run with verbose logging and visible browser for debugging:
```bash
python enhanced_pulte_scraper.py --verbose --no-headless
```

This will show detailed logs and let you see what the browser is doing.

## ⚖️ Legal and Ethical Considerations

- **Respect robots.txt**: Check the website's robots.txt file
- **Rate limiting**: The scraper includes delays to avoid overwhelming the server
- **Terms of service**: Make sure your use complies with the website's terms
- **Data usage**: Only use scraped data for legitimate purposes
- **Attribution**: Consider giving credit when using the data

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the scraper.

## 📝 License

This project is provided as-is for educational and research purposes.

## 🔄 Updates

- **v2.0**: Enhanced scraper with multiple strategies and better error handling
- **v1.0**: Basic scraper with Selenium support

---

**Happy scraping! 🎉**

For questions or issues, please check the troubleshooting section or create an issue in the repository. 