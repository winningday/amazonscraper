# Amazon Kindle Scraper

## Overview

This is a Python-based Amazon Kindle book scraper designed to extract various details from Amazon product pages such as:
- Title
- Author
- Format
- Summary
- Print Length
- ASIN
- Publisher
- Publication Date
- Best Sellers Rank
- Amazon Rating
- Amazon Number of Ratings
- Goodreads Rating
- Goodreads Number of Ratings

The scraper uses **Selenium** for interacting with Amazon’s dynamic content, **BeautifulSoup** for parsing the HTML, and other libraries for handling the data and simulating human-like browsing to avoid detection.

## Features
- Automatic retries for failed URLs.
- Captures detailed product information, including Goodreads data.
- Supports headless Chrome mode for running without displaying the browser.
- Dynamic CSV generation: each product is written to the CSV file as soon as it’s scraped.
- Automatic login via cookies, with manual login fallback.
- Error handling with logging for failed URLs, including retry attempts.

## Requirements

To run the scraper, ensure that you have the following Python libraries installed:

```bash
pip install beautifulsoup4 requests pandas fake_useragent selenium
```

Other dependencies:
- **Chrome**: The scraper requires a working version of Chrome to run.
- **Chromedriver**: ChromeDriver must be installed and set with correct permissions for your OS (especially on macOS). More info can be found at https://developer.chrome.com/docs/chromedriver/downloads
- **Fake User Agent**: This library randomizes the user agent to simulate different browsing environments.

## Installation

1. Clone this repository:

```bash
git clone https://github.com/winningday/amazonscraper.git
cd amazonscraper
```

2. Install the required Python libraries:

```bash
pip install -r requirements.txt
```

3. **MacOS Users Only**: Ensure the `chromedriver` file has the correct permissions. Run the following command:

```bash
chmod +x chromedriver-mac-arm64/chromedriver
```

4. Set up your `chromedriver` for Selenium by downloading the appropriate version of ChromeDriver from [here](https://googlechromelabs.github.io/chrome-for-testing/) and placing it in the repository directory. Make sure it matches your version of Chrome.

## Usage

1. **CSV Input**:
    - The scraper reads URLs from a CSV file named `kindle_books.csv`. The CSV should contain a column `Amazon_URL` with the product URLs to scrape.

2. **Run the Scraper**:

    ```bash
    python amazonscraper.py
    ```

3. **Manual Login**:
   If prompted, log in manually on the Chrome window that appears. This is necessary for retrieving some product information, like Goodreads ratings, which require an authenticated session.
   - If user does not wish to login to get Goodreads data, then user can run without logging method as follows:
   ```bash
   python amazonscraper.py --no-login
   ```

4. **View Results**:
   After the process is complete, results will be saved in `scraped_amazon_data.csv` and any failed URLs will be in `failed_urls.csv`.

5. **Command-Line Arguments**:
    | Argument | Description |
    |----------|-------------|
    | `--no-login` | Skip the login process. Goodreads data will not be scraped.  |

## How It Works

1. **Amazon Login (Optional)g**: 
    - The program logs into Amazon by default to scrape Goodreads data. If you are already logged in, it uses cookies stored from a previous session.
    - If user does not wish to login then at the command line they should enter: 
        ```bash
        python amazonscraper.py --no-login
        ```

2. **Headless Mode**:
    - The scraper can run in headless mode, where the browser UI is not displayed. This makes the process more efficient for large-scale scraping.
   
3. **Scraping Process**:
    - It scrapes the required product details using Selenium and BeautifulSoup
    - The scraper reads a CSV file (`kindle_books.csv`) containing a list of Amazon product URLs.
    - It scrapes the details of each product and saves the results to `scraped_amazon_data.csv`.
    - If any URLs fail, they are retried a set number of times. Failed URLs after retries are saved to a separate `failed_urls.csv` file.

4. **Error Handling**:
    - If a URL fails to scrape, it retries the URL up to 3 times. After 3 failed attempts, the URL is logged in failed_urls.csv.

## Requirements:
    - Python 3.x
    - Chrome Browser
    - ChromeDriver (Ensure the version matches your installed Chrome Browser)

## Dependencies:
The required packages are listed in `requirements.txt`:
```bash
beautifulsoup4
selenium
pandas
fake_useragent
requests
```
You can install them using:

```bash
pip install -r requirements.txt
```
## License
This project is licensed under the MIT License - see the [LICENSE](https://github.com/winningday/amazonscraper/blob/main/LICENSE) file for details.

## Troubleshooting

- **Permissions Issues with ChromeDriver**: If you encounter an error related to ChromeDriver permissions, make sure you have set the correct execution permissions using:

```bash
chmod +x chromedriver-mac-arm64/chromedriver
```

- **Amazon Blocking**: Amazon has strict scraping policies. If you encounter frequent captchas or other blockages, consider adding longer sleep delays or using a proxy service.
