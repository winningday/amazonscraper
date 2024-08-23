import pytest
import os
import pickle
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
from amazonscraper import (
    scrape_amazon_product,
    clean_url,
    check_for_captcha,
    is_valid_product_data,
    scrape_amazon,
    retry_failed_urls,
    switch_browser_mode,
    save_cookies,
    load_cookies,
    login_and_save_cookies,
)

# Test clean_url
@pytest.mark.parametrize("url, expected", [
    ("https://www.amazon.com/product/ref=something", "https://www.amazon.com/product/"),
    ("https://www.amazon.com/anotherproduct/", "https://www.amazon.com/anotherproduct/"),
])
def test_clean_url(url, expected):
    assert clean_url(url) == expected

# Test is_valid_product_data
def test_is_valid_product_data():
    valid_data = {
        'Title': 'Valid Book',
        'Author': 'Author Name',
        'Format': 'Paperback',
        'ASIN': '1234567890',
        'Amazon Rating': '4.5'
    }
    invalid_data = {
        'Title': '#ERROR',
        'Author': '#ERROR',
        'Format': '#ERROR',
        'ASIN': '#ERROR',
        'Amazon Rating': '#ERROR'
    }
    assert is_valid_product_data(valid_data) == True
    assert is_valid_product_data(invalid_data) == False

# Test save_cookies
@patch("builtins.open", new_callable=mock_open)
@patch("amazonscraper.pickle.dump")
def test_save_cookies(mock_pickle_dump, mock_file):
    mock_driver = MagicMock()
    mock_driver.get_cookies.return_value = [{'cookie': 'data'}]

    save_cookies(mock_driver, 'cookies.pkl')

    mock_file.assert_called_once_with('cookies.pkl', 'wb')
    mock_pickle_dump.assert_called_once_with(mock_driver.get_cookies(), mock_file())

# Test load_cookies
@patch("builtins.open", new_callable=mock_open)
@patch("amazonscraper.pickle.load")
def test_load_cookies(mock_pickle_load, mock_file):
    mock_driver = MagicMock()
    mock_pickle_load.return_value = [{'domain': 'amazon.com', 'cookie': 'data'}]

    load_cookies(mock_driver, 'cookies.pkl')

    mock_file.assert_called_once_with('cookies.pkl', 'rb')
    mock_pickle_load.assert_called_once_with(mock_file())
    mock_driver.add_cookie.assert_called_once_with({'domain': 'amazon.com', 'cookie': 'data'})

# Test login_and_save_cookies
@patch('amazonscraper.input', create=True)
@patch('amazonscraper.save_cookies')
def test_login_and_save_cookies(mock_save_cookies, mock_input):
    mock_input.return_value = "done"  # Mock the input to simulate user input
    mock_driver = MagicMock()
    mock_driver.get = MagicMock()

    login_and_save_cookies(mock_driver)

    mock_driver.get.assert_called_once_with('https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_custrec_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0')
    mock_save_cookies.assert_called_once_with(mock_driver, 'amazon_cookies.pkl')

# Mock scrape_amazon_product
@patch('amazonscraper.webdriver.Chrome')
def test_scrape_amazon_product(mock_webdriver):
    mock_driver = MagicMock()
    mock_webdriver.return_value = mock_driver

    # Mocking the page source with a valid HTML structure
    mock_driver.page_source = """
    <html>
        <div id="productTitle">Test Product</div>
        <div id="bylineInfo"><a>Test Author</a></div>
        <span class="a-icon-alt">4.5 out of 5 stars</span>
    </html>
    """
    result = scrape_amazon_product(mock_driver, "https://www.amazon.com/test-product")

    assert result['Title'] == 'Test Product'
    assert result['Author'] == 'Test Author'
    assert result['Amazon Rating'] == '4.5'

# Mock check_for_captcha
@patch('amazonscraper.input', return_value='done')
@patch('amazonscraper.webdriver.Chrome')
def test_check_for_captcha(mock_webdriver, mock_input):
    mock_driver = MagicMock()
    mock_webdriver.return_value = mock_driver
    
    # Mock CAPTCHA presence in page source
    mock_driver.page_source = "CAPTCHA"
    assert check_for_captcha(mock_driver) == True
    
    # Mock no CAPTCHA
    mock_driver.page_source = "Normal page content"
    assert check_for_captcha(mock_driver) == False

# Test retry logic
@patch('amazonscraper.scrape_amazon_product')
def test_retry_failed_urls(mock_scrape_product, mocker):
    # Simulate scraping failures and successes
    mock_scrape_product.side_effect = [Exception("Fail"), Exception("Fail"), {"Title": "Success"}]
    
    mock_driver = MagicMock()
    failed_urls = ["https://www.amazon.com/test-product"]
    
    retry_failed_urls(mock_driver, failed_urls, "mock_output.csv", max_retries=3)

    # Ensure scrape_amazon_product was called 3 times
    assert mock_scrape_product.call_count == 3

# Test switch_browser_mode
@patch('amazonscraper.webdriver.Chrome')
def test_switch_browser_mode(mock_webdriver):
    service = MagicMock()
    ua = MagicMock()
    
    # Test headless mode on
    driver = switch_browser_mode(service, headless=True, ua=ua)
    mock_webdriver.assert_called_once()

    # Test headless mode off
    driver = switch_browser_mode(service, headless=False, ua=ua)
    mock_webdriver.assert_called()

# Mock scrape_amazon function
@patch('amazonscraper.scrape_amazon_product')
@patch('amazonscraper.webdriver.Chrome')
def test_scrape_amazon(mock_webdriver, mock_scrape_product, mocker):
    # Mock data and driver
    mock_driver = MagicMock()
    mock_webdriver.return_value = mock_driver
    mock_scrape_product.return_value = {
        'Title': 'Test Product',
        'Author': 'Test Author',
        'Format': 'Paperback',
        'ASIN': '1234567890',
        'Amazon Rating': '4.5'
    }

    # Mock CSV reading
    mock_csv = pd.DataFrame({'Amazon_URL': ["https://www.amazon.com/test-product"]})
    mocker.patch('pandas.read_csv', return_value=mock_csv)
    
    service = MagicMock()
    ua = MagicMock()

    # Run scrape_amazon with mocked data
    scrape_amazon(mock_driver, 'mock_input.csv', service, ua)

    # Ensure scrape_amazon_product was called once
    mock_scrape_product.assert_called_once()

# Mock the CAPTCHA handling in scrape_amazon
@patch('pandas.read_csv')
@patch('amazonscraper.input', return_value='done')  # Mock input to avoid manual interaction
@patch('amazonscraper.check_for_captcha')
@patch('amazonscraper.scrape_amazon_product')
@patch('amazonscraper.webdriver.Chrome')
def test_scrape_amazon_with_captcha(mock_webdriver, mock_scrape_product, mock_check_for_captcha, mock_input, mock_read_csv):
    # Mock data and driver
    mock_driver = MagicMock()
    mock_webdriver.return_value = mock_driver
    mock_scrape_product.return_value = {
        'Title': 'Test Product',
        'Author': 'Test Author',
        'Format': 'Paperback',
        'ASIN': '1234567890',
        'Amazon Rating': '4.5'
    }

    # Simulate CAPTCHA detection on the first try and no CAPTCHA on the second and third
    mock_check_for_captcha.side_effect = [True, False, False]  # Adjust to handle CAPTCHA on the first try only

    # Mock the CSV read to avoid the FileNotFoundError
    mock_read_csv.return_value = pd.DataFrame({'Amazon_URL': ["https://www.amazon.com/test-product"]})

    service = MagicMock()
    ua = MagicMock()

    # Run scrape_amazon with mocked data
    scrape_amazon(mock_driver, 'mock_input.csv', service, ua)

    # Ensure scrape_amazon_product was called once after CAPTCHA was handled
    assert mock_scrape_product.call_count == 1

    # Check how many times CAPTCHA checking logic was called
    assert mock_check_for_captcha.call_count == 2  # Expecting 2 calls since CAPTCHA is handled
