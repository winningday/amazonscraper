"""
Amazon Kindle Scraper
Requirements:
pip install beautifulsoup4 requests pandas fake_useragent selenium

Install necessary packages:

beautifulsoup4 for HTML parsing.
requests for making HTTP requests.
pandas to handle the CSV of URLs.
fake_useragent to randomize user agents and time to add  delays between 
requests.

Scraping Amazon is challenging due to their strong anti-scraping policies, 
so implemented some strategies to avoid getting flagged. 
This includes simulating human-like behavior by adding delays between 
requests, randomizing the user-agent, adding Captcha detection to
allow manual user input, and a few others.

To scrape from Amazon, used Python libraries like BeautifulSoup 
for parsing and requests for making HTTP requests. However, since Amazon 
often obfuscates its HTML structure or employs dynamic loading for 
certain elements (like reviews and ratings), also had to work 
with Selenium.
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import pickle
import numpy as np
from urllib.parse import urlparse
import random
import os
import argparse


# Utility functions for cookies
def save_cookies(driver, cookies_file):
    with open(cookies_file, "wb") as file:
        pickle.dump(driver.get_cookies(), file)


def load_cookies(driver, cookies_file):
    with open(cookies_file, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            # Ensure we are adding cookies for the amazon.com domain
            if "amazon.com" in cookie["domain"]:
                try:
                    driver.add_cookie(cookie)
                    # print(f"Loaded cookie for domain: {cookie['domain']}")
                except Exception as e:
                    print(f"Error loading cookie for domain {cookie['domain']}: {e}")


# Login manually and save cookies
def login_and_save_cookies(driver):
    driver.get(
        "https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_custrec_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
    )
    input("Please log in manually and press Enter after completing login...")
    save_cookies(driver, "amazon_cookies.pkl")


# Clean URL function
def clean_url(url):
    parsed_url = urlparse(url)
    # Doc: https://docs.python.org/3/library/urllib.parse.html
    clean_path = parsed_url.path.split("/ref")[0].rstrip("/")  
    # Remove anything after /ref and trailing slash if it exists
    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{clean_path}"
    if not clean_path.endswith("/"):
        clean_url += "/"
    return clean_url


# Function to scrape the Amazon product
def scrape_amazon_product(driver, url):
    driver.get(url)

    # Check for CAPTCHA
    if check_for_captcha(driver):
        return "CAPTCHA"

    # Trying to fix sometimes page not loading and no data scraped
    try:
        # Wait for the page to load, but continue if the element is not found
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "reviewFeatureGroup"))
        )
    except Exception as e:
        print(
            f"Warning: Timeout or element not found on {url}, proceeding with scraping available data."
        )

    # Scroll to simulate human behavior
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(5, 10))

    # Get page source
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # Debugging: Print page source
    # print("Page Source loaded successfully.")

    # Extract Goodreads section and handle errors
    try:
        goodreads_section = soup.find("div", class_="gr-review-base")
        if goodreads_section:
            # print("Goodreads Section Found")
            goodreads_rating = (
                goodreads_section.find("div", class_="gr-review-rating-text")
                .find("span")
                .get_text(strip=True)
            )
            goodreads_num_ratings = (
                goodreads_section.find("div", class_="gr-review-count-text")
                .find("span")
                .get_text(strip=True)
                .replace(",", "")
                .split()[0]
            )
        else:
            # print("Goodreads Section Not Found.")
            goodreads_rating = np.nan
            goodreads_num_ratings = np.nan
    except Exception as e:
        print(f"Error extracting Goodreads data: {e}")
        goodreads_rating = "#ERROR"
        goodreads_num_ratings = "#ERROR"

    # Try to extract each piece of information and handle if it doesn't exist
    try:
        title = soup.select_one("#productTitle").get_text(strip=True)
    except AttributeError:
        title = "#ERROR"

    try:
        author = soup.select_one("#bylineInfo a").get_text(strip=True)
    except AttributeError:
        author = "#ERROR"

    try:
        format_type = soup.select_one(
            "#bylineInfo span.a-color-secondary ~ span"
        ).get_text(strip=True)
    except AttributeError:
        format_type = "#ERROR"

    try:
        summary_section = soup.select_one(".a-expander-content")
        summary = summary_section.get_text(strip=True) if summary_section else "NA"
    except AttributeError:
        summary = "#ERROR"

    try:
        print_length_section = soup.select_one(
            "#rpi-attribute-book_details-ebook_pages .rpi-attribute-value span"
        )
        print_length = (
            print_length_section.get_text(strip=True).split()[0]
            if print_length_section
            else "NA"
        )
    except AttributeError:
        print_length = "#ERROR"

    try:
        asin_section = soup.find("span", string=lambda text: text and "ASIN" in text)
        asin = (
            asin_section.find_next("span").get_text(strip=True)
            if asin_section
            else "NA"
        )
    except AttributeError:
        asin = "#ERROR"

    try:
        publisher_section = soup.find(
            "span", string=lambda text: text and "Publisher" in text
        )
        publisher = (
            publisher_section.find_next("span").get_text(strip=True)
            if publisher_section
            else "NA"
        )
    except AttributeError:
        publisher = "#ERROR"

    try:
        pub_date_section = soup.select_one(
            "#rpi-attribute-book_details-publication_date .rpi-attribute-value span"
        )
        pub_date_text = (
            pub_date_section.get_text(strip=True) if pub_date_section else "NA"
        )
        pub_date = (
            pd.to_datetime(pub_date_text).strftime("%m/%d/%Y")
            if pub_date_text != "NA"
            else pub_date_text
        )
    except (AttributeError, ValueError):
        pub_date = "#ERROR"

    try:
        best_sellers_rank = soup.select_one(".zg_hrsr .a-list-item").get_text(
            strip=True
        )
    except AttributeError:
        best_sellers_rank = "#ERROR"

    try:
        rating = soup.select_one(".a-icon-alt").get_text(strip=True).split()[0]
    except AttributeError:
        rating = "#ERROR"

    try:
        num_ratings = (
            soup.select_one("#acrCustomerReviewText").get_text(strip=True).split()[0]
        )
    except AttributeError:
        num_ratings = "#ERROR"

    # Clean the URL and remove any /ref values...
    cleaned_url = clean_url(url)

    # Compile the results into a dictionary
    result = {
        "URL": cleaned_url,  # Add the cleaned URL here
        "Title": title,
        "Author": author,
        "Format": format_type,
        "Summary": summary,
        "Print Length": print_length,
        "ASIN": asin,
        "Publisher": publisher,
        "Publication Date": pub_date,
        "Best Sellers Rank": best_sellers_rank,
        "Amazon Rating": rating,
        "Amazon # of Ratings": num_ratings,
        "Goodreads Rating": goodreads_rating,
        "Goodreads # of Ratings": goodreads_num_ratings,
    }
    return result


# Function to scrape Amazon with retries and dynamic CSV writing
def scrape_amazon(driver, csv_file, service, ua=None):
    df = pd.read_csv(csv_file)
    failed_urls = []
    csv_output = "scraped_amazon_data.csv"

    # Check if CSV exists, if not create it with headers
    if not os.path.exists(csv_output):
        pd.DataFrame(
            columns=[
                "URL",
                "Title",
                "Author",
                "Format",
                "Summary",
                "Print Length",
                "ASIN",
                "Publisher",
                "Publication Date",
                "Best Sellers Rank",
                "Amazon Rating",
                "Amazon # of Ratings",
                "Goodreads Rating",
                "Goodreads # of Ratings",
            ]
        ).to_csv(csv_output, index=False)

    # Scrape each URL
    for index, row in df.iterrows():
        amazon_url = row["Amazon_URL"]
        print(f"Scraping Amazon: {amazon_url}")

        try:
            # Check for CAPTCHA before scraping
            if check_for_captcha(driver):
                print("CAPTCHA detected. Switching to visible mode for manual solving.")
                # Switch to visible mode for CAPTCHA solving
                driver.quit()
                driver = switch_browser_mode(service, headless=False, ua=ua)
                driver.get(amazon_url)
                input("Please solve the CAPTCHA and press Enter when done...")
                driver.quit()
                # Switch back to headless mode after CAPTCHA is solved
                driver = switch_browser_mode(service, headless=True, ua=ua)

                # ** Add second CAPTCHA check here ** after switching back to headless
                if check_for_captcha(driver):
                    print(
                        "CAPTCHA detected again after switching back to headless mode."
                    )
                    # Handle additional CAPTCHA logic if needed
                    return "CAPTCHA"

            # Attempt scraping after CAPTCHA check
            product_data = scrape_amazon_product(driver, amazon_url)
            # If CAPTCHA detected during scraping
            if product_data == "CAPTCHA":
                print("CAPTCHA encountered again, switching modes to handle it.")
                # Switch to visible mode
                driver.quit()
                driver = switch_browser_mode(service, headless=False, ua=ua)
                driver.get(amazon_url)
                input("Please solve the CAPTCHA and press Enter when done...")
                driver.quit()
                # Switch back to headless mode
                driver = switch_browser_mode(service, headless=True, ua=ua)
                # Retry scraping
                product_data = scrape_amazon_product(driver, amazon_url)

            # Validate and save scraped product data
            if is_valid_product_data(product_data):
                pd.DataFrame([product_data]).to_csv(
                    csv_output, mode="a", header=False, index=False
                )  # Append each result to CSV
            else:
                print(f"Invalid data scraped for {amazon_url}")
                failed_urls.append(amazon_url)
        except Exception as e:
            print(f"Error scraping {amazon_url}: {e}")
            failed_urls.append(amazon_url)  # Log failed URL

    # Retry failed URLs if any
    if failed_urls:
        print(f"Retrying {len(failed_urls)} failed URLs...")
        retry_failed_urls(driver, failed_urls, csv_output)


def is_valid_product_data(product_data):
    # Check if most of the important fields are not "#ERROR"
    important_fields = ["Title", "Author", "Format", "ASIN", "Amazon Rating"]
    valid_fields = sum(
        1 for field in important_fields if product_data[field] != "#ERROR"
    )
    return (
        valid_fields >= 3
    )  # Consider valid if at least 3 important fields are scraped


# Retry function for failed URLs
def retry_failed_urls(driver, failed_urls, csv_output, max_retries=3):
    retry_failures = []
    for url in failed_urls:
        success = False
        for attempt in range(max_retries):
            print(f"Retrying {url}, attempt {attempt + 1}")
            try:
                product_data = scrape_amazon_product(driver, url)
                if is_valid_product_data(product_data):
                    pd.DataFrame([product_data]).to_csv(
                        csv_output, mode="a", header=False, index=False
                    )  # Append retried result
                    success = True
                    break
                else:
                    print(
                        f"Invalid data scraped for {url} on retry attempt {attempt + 1}"
                    )
            except Exception as e:
                print(f"Retry {attempt + 1} failed for {url}: {e}")
        if not success:
            retry_failures.append(url)  # Log URLs that failed after retries

    # Save failed URLs to CSV if any
    if retry_failures:
        pd.DataFrame(retry_failures, columns=["Failed URLs"]).to_csv(
            "failed_urls.csv", index=False
        )
        print(f"Failed URLs after retries saved to 'failed_urls.csv'.")


def check_for_captcha(driver):
    # Function to check whenever a CAPTCHA might appear in a page
    if "captcha" in driver.page_source.lower():
        print("CAPTCHA detected. Please solve it manually.")
        input("Please solve the CAPTCHA and press Enter when done...")
        return True
    return False


def switch_browser_mode(service, headless=True, ua=None):
    # Function to switch to headless and back and forth, useful if a CAPTCHA found
    chrome_options = Options()
    if ua is None:
        ua = UserAgent()  # Generate a new user agent if not passed
    chrome_options.add_argument(f"user-agent={ua.random}")
    if headless:
        chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def main():
    # Start timer
    start_time = time.time()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Amazon Scraper with optional Amazon login for Goodreads data."
    )
    parser.add_argument(
        "--no-login",
        action="store_true",
        help="Skip login to Amazon (Goodreads data will not be scraped)",
    )
    args = parser.parse_args()

    # Setup Chrome options for Selenium
    ua = UserAgent()
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={ua.random}")

    webdriver_path = "./chromedriver-mac-arm64/chromedriver"
    service = Service(webdriver_path)

    # Perform login by default unless --no-login flag is passed
    if not args.no_login:
        driver = switch_browser_mode(
            service, headless=False, ua=ua
        )  # Start in non-headless mode for login
        # Load amazon and cookies
        driver.get("https://www.amazon.com/")

        # Check for CAPTCHA
        if check_for_captcha(driver):
            input("Please solve the CAPTCHA and press Enter when done...")

        try:
            load_cookies(driver, "amazon_cookies.pkl")
            # print("Cookies loaded successfully.")
        except FileNotFoundError:
            print("Cookies not found, logging in manually...")
            login_and_save_cookies(driver)

        # Check if logged in
        driver.get(
            "https://www.amazon.com/gp/css/homepage.html"
        )  # Navigate to an account page that requires login
        if "Sign In" in driver.page_source or "Sign-In" in driver.title:
            print("Not logged in, prompting for manual login...")
            login_and_save_cookies(driver)  # Trigger manual login and save cookies

        # Close the UI driver after login
        driver.quit()

    else:
        print("Skipping login, Goodreads data will not be scraped.")

    # Reinitialize driver for scraping
    driver = switch_browser_mode(
        service, headless=True, ua=ua
    )  # Switch to headless for scraping

    # Check for CAPTCHA before starting scraping
    driver.get("https://www.amazon.com/")
    if check_for_captcha(driver):
        # Switch to visible mode for CAPTCHA
        driver.quit()
        driver = switch_browser_mode(service, headless=False, ua=ua)
        driver.get("https://www.amazon.com/")
        input("Please solve the CAPTCHA and press Enter when done...")

        driver.quit()
        driver = switch_browser_mode(service, headless=True, ua=ua)

    # Provide CSV file containing URLs
    csv_file = "kindle_books.csv"

    # Run the scraping process
    scrape_amazon(driver, csv_file, service, ua)

    driver.quit()

    # End timer
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(
        f"Scraping completed and saved to 'scraped_amazon_data.csv' in {elapsed_time:.2f} seconds."
    )


if __name__ == "__main__":
    main()
