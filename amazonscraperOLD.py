'''
Amazon Kindle Scraper
Requirements:
pip install beautifulsoup4 requests pandas fake_useragent selenium

Install necessary packages:

beautifulsoup4 for HTML parsing.
requests for making HTTP requests.
pandas to handle the CSV of URLs.
Optionally, fake_useragent to randomize user agents and time to add 
delays between requests.

Scraping Amazon is challenging due to their strong anti-scraping policies, 
so we'll need to implement some strategies to avoid getting flagged. 
This includes simulating human-like behavior by adding delays between 
requests, randomizing the user-agent, and possibly using proxies.

To scrape from Amazon, we'll use Python libraries like BeautifulSoup 
for parsing and requests for making HTTP requests. However, since Amazon 
often obfuscates its HTML structure or employs dynamic loading for 
certain elements (like reviews and ratings), we may also need to work 
with tools like Selenium if necessary.


'''

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

def save_cookies(driver, cookies_file):
    with open(cookies_file, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)

def load_cookies(driver, cookies_file):
    with open(cookies_file, 'rb') as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            # Only load cookies that match the domain 'amazon.com'
            if 'domain' in cookie and '.amazon.com' in cookie['domain']:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie for domain {cookie['domain']}: {e}")



def login_and_save_cookies():
    chrome_options = Options()
    # Disable headless mode for manual login
    webdriver_path = './chromedriver-mac-arm64/chromedriver'
    service = Service(webdriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Load Amazon login page
    driver.get('https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_custrec_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0')

    # Wait for manual login (or set an explicit wait for the login page)
    input("Please log in manually and press Enter after completing login...")
    
    # Save the cookies once logged in
    save_cookies(driver, 'amazon_cookies.pkl')
    
    driver.quit()

# Function to clean up URL and remove any ref code after it
def clean_url(url):
    parsed_url = urlparse(url)
    # Remove anything after /product/<ASIN>/
    clean_path = parsed_url.path.split('/ref')[0]  # Remove anything after /ref
    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{clean_path}/"
    return clean_url

"""
# Function to scrape a single Amazon page
def scrape_amazon_product(driver, url):
    # Load the page
    driver.get(url)
    # time.sleep(2)  # Wait for the page to load completely
    # Wait explicitly for the page to load completely
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "reviewFeatureGroup"))
    )

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Try to extract each piece of information and handle if it doesn't exist
    try:
        title = soup.select_one('#productTitle').get_text(strip=True)
    except AttributeError:
        title = "No title available"

    try:
        author = soup.select_one('#bylineInfo a').get_text(strip=True)
    except AttributeError:
        author = "No author available"

    try:
        format_type = soup.select_one('#bylineInfo span.a-color-secondary ~ span').get_text(strip=True)
    except AttributeError:
        format_type = "No format available"

    try:
        summary_section = soup.select_one('.a-expander-content')
        summary = summary_section.get_text(strip=True) if summary_section else "No summary available."
    except AttributeError:
        summary = "No summary available"

    try:
        print_length_section = soup.select_one('#rpi-attribute-book_details-ebook_pages .rpi-attribute-value span')
        print_length = print_length_section.get_text(strip=True).split()[0] if print_length_section else "No print length available"
    except AttributeError:
        print_length = "No print length available"

    try:
        asin_section = soup.find('span', string=lambda text: text and "ASIN" in text)
        asin = asin_section.find_next('span').get_text(strip=True) if asin_section else "No ASIN available"
    except AttributeError:
        asin = "No ASIN available"

    try:
        publisher_section = soup.find('span', string=lambda text: text and "Publisher" in text)
        publisher = publisher_section.find_next('span').get_text(strip=True) if publisher_section else "No publisher available"
    except AttributeError:
        publisher = "No publisher available"

    try:
        pub_date_section = soup.select_one('#rpi-attribute-book_details-publication_date .rpi-attribute-value span')
        pub_date_text = pub_date_section.get_text(strip=True) if pub_date_section else "No publication date available"
        pub_date = pd.to_datetime(pub_date_text).strftime('%m/%d/%Y') if pub_date_text != "No publication date available" else pub_date_text
    except (AttributeError, ValueError):
        pub_date = "No publication date available"

    try:
        best_sellers_rank = soup.select_one('.zg_hrsr .a-list-item').get_text(strip=True)
    except AttributeError:
        best_sellers_rank = "No best sellers rank available"

    try:
        rating = soup.select_one('.a-icon-alt').get_text(strip=True).split()[0]
    except AttributeError:
        rating = "No rating available"

    try:
        num_ratings = soup.select_one('#acrCustomerReviewText').get_text(strip=True).split()[0]
    except AttributeError:
        num_ratings = "No number of ratings available"


    # Following didn't working
    # try:
    #     goodreads_section = soup.select_one('.gr-review-base')
    #     if goodreads_section:
    #         goodreads_rating = goodreads_section.select_one('.gr-review-rating-text span').get_text(strip=True).split()[0]
    #         goodreads_num_ratings = goodreads_section.select_one('.gr-review-count-text span').get_text(strip=True).split()[0]
    #     else:
    #         goodreads_rating = np.nan
    #         goodreads_num_ratings = np.nan
    # except AttributeError:
    #     goodreads_rating = np.nan
    #     goodreads_num_ratings = np.nan

    # Suspect goodreads loads with a javascript when the page is loaded,
    # so we can try using Selenium directly to get Goodreads rating and number of ratings
    # Goodreads information using Selenium directly
    # Try extracting Goodreads section
    # try:
    #     goodreads_section = soup.find('div', class_='gr-review-base')
    #     if goodreads_section:
    #         print("Goodreads Section Found:")
    #         print(goodreads_section.prettify())  # Log the HTML for debugging
            
    #         goodreads_rating = goodreads_section.find('div', class_='gr-review-rating-text').find('span', class_='a-size-base').get_text(strip=True)
    #         goodreads_num_ratings = goodreads_section.find('div', class_='gr-review-count-text').find('span', class_='a-size-base').get_text(strip=True).replace(',', '').split()[0]
    #     else:
    #         goodreads_rating = np.nan
    #         goodreads_num_ratings = np.nan
    # except Exception as e:
    #     print(f"Error extracting Goodreads data: {e}")
    #     goodreads_rating = np.nan
    #     goodreads_num_ratings = np.nan


    cleaned_url = clean_url(url)

    # Compile the results into a dictionary
    result = {
        'URL': cleaned_url,  # Add the cleaned URL here
        'Title': title,
        'Author': author,
        'Format': format_type,
        'Summary': summary,
        'Print Length': print_length,
        'ASIN': asin,
        'Publisher': publisher,
        'Publication Date': pub_date,
        'Best Sellers Rank': best_sellers_rank,
        'Amazon Rating': rating,
        'Amazon Number of Ratings': num_ratings,
        'Goodreads Rating': goodreads_rating,
        'Goodreads Number of Ratings': goodreads_num_ratings,
    }
    return result


"""

# Function to read URLs from CSV and scrape data for each one
def scrape_amazon(driver, csv_file):
    # Read the CSV file
    df = pd.read_csv(csv_file)

    # List to hold all scraped data
    scraped_data = []

    # Loop through the URLs in the CSV file
    for index, row in df.iterrows():
        amazon_url = row['Amazon_URL']
        print(f"Scraping Amazon: {amazon_url}")
        
        try:
            # Scrape Amazon
            product_data = scrape_amazon_product(driver, amazon_url)
            scraped_data.append(product_data)
        except Exception as e:
            print(f"Error scraping {amazon_url}: {e}")

    # Convert to DataFrame for saving to CSV or further processing
    scraped_df = pd.DataFrame(scraped_data)
    return scraped_df

# Debugging function:
def scrape_amazon_product(driver, url):
    # Navigate to the base Amazon domain first to match the cookie domain
    driver.get("https://www.amazon.com")
    
    # Load cookies for logged-in session
    load_cookies(driver, 'amazon_cookies.pkl')

    # Reload the page after adding cookies
    driver.get(url)

    # Wait explicitly for the page to load completely
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "reviewFeatureGroup"))
    )
    # Scroll the page to make it look like a human is interacting
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Add a delay after scrolling to simulate human behavior

    # Sleep for a random time between 5 and 10 seconds to simulate human behavior
    time.sleep(random.uniform(5, 10))

    # Print the page source for inspection
    page_source = driver.page_source
    print("Page Source:", page_source)


    # Parse the page with BeautifulSoup for other elements
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # Attempt to find the Goodreads section
    goodreads_section = soup.find('div', class_='gr-review-base')
    if goodreads_section:
        print("Goodreads Section Found:")
        print(goodreads_section.prettify())
    else:
        print("Goodreads Section Not Found.")

    # Goodreads extraction with explicit wait
    try:
        # Goodreads rating
        goodreads_rating_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='gr-review-rating-text']//span"))
        )
        goodreads_rating = goodreads_rating_section.text.strip()

        # Goodreads number of ratings
        goodreads_num_ratings_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='gr-review-count-text']//span"))
        )
        goodreads_num_ratings = goodreads_num_ratings_section.text.strip().replace(',', '').split()[0]

        print(f"Goodreads Rating: {goodreads_rating}, Goodreads Number of Ratings: {goodreads_num_ratings}")

    except Exception as e:
        print(f"Error extracting Goodreads data: {e}")
        goodreads_rating = np.nan
        goodreads_num_ratings = np.nan

    # Compile the results into a dictionary
    result = {
        'URL': url,
        'Goodreads Rating': goodreads_rating,
        'Goodreads Number of Ratings': goodreads_num_ratings,
    }
    return result

def main():
    login_and_save_cookies()

    # Set up Chrome options for Selenium (optional: run headless if you don't need to see the browser)
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode (no UI)

    # Set a random user-agent using the fake_useragent library
    ua = UserAgent()
    chrome_options.add_argument(f'user-agent={ua.random}')

    # Path to your Chrome WebDriver
    webdriver_path = './chromedriver-mac-arm64/chromedriver'

    # Set up Selenium WebDriver
    service = Service(webdriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Ensure we are on amazon.com before loading cookies
    driver.get('https://www.amazon.com/')
    
    # Check if cookies exist, if not, log in manually and save cookies
    try:
        load_cookies(driver, 'amazon_cookies.pkl')
        print("Cookies loaded successfully.")
    except FileNotFoundError:
        print("Cookies not found, logging in manually...")
        login_and_save_cookies()
    
    # Reload the page after adding cookies to check if login persists
    driver.get('https://www.amazon.com/')

    # Provide the path to the CSV file containing the URLs
    csv_file = 'kindle_books.csv'

    # Run the scraping process
    scraped_data_df = scrape_amazon(driver, csv_file)

    # Save the data to a new CSV file
    scraped_data_df.to_csv('scraped_amazon_data.csv', index=False)

    # Close the WebDriver
    driver.quit()

    print("Scraping completed and saved to 'scraped_amazon_data.csv'")

if __name__ == "__main__":
    main()