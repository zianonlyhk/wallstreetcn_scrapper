from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import concurrent.futures
import threading
from typing import List, Dict


# Thread-local storage for WebDriver instances
thread_local = threading.local()


def get_driver():
    """Get or create a WebDriver instance for the current thread"""
    if not hasattr(thread_local, 'driver'):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-images')  # Faster loading
        chrome_options.add_argument('--disable-css')    # Skip CSS loading
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-javascript')  # Skip JS if not needed
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        chrome_options.add_argument('--page-load-strategy=eager')  # Don't wait for all resources
        
        thread_local.driver = webdriver.Chrome(options=chrome_options)
        thread_local.driver.implicitly_wait(5)  # Reduced wait time
        thread_local.driver.set_page_load_timeout(20)  # Set page load timeout
    
    return thread_local.driver


def cleanup_driver():
    """Clean up the WebDriver instance for the current thread"""
    if hasattr(thread_local, 'driver'):
        try:
            thread_local.driver.quit()
        except:
            pass
        finally:
            delattr(thread_local, 'driver')


def scrape_single_url(url: str) -> str:
    """Scrape content from a single URL using thread-local WebDriver"""
    driver = get_driver()
    
    try:
        # Load the page with timeout
        driver.get(url)
        
        # Wait for article element with shorter timeout
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'article'))
        )
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Initialize data dictionary
        article_data = {
            "title": "",
            "date": "",
            "content": "",
            "source_url": url
        }
        
        # Extract title - optimized selectors
        title_selectors = ['article h1', 'h1.article-title', 'h1']
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                article_data["title"] = title_element.get_text(strip=True)
                break
        
        # Extract date - optimized selectors
        date_selectors = [
            'article time[datetime]',
            'article .date', 
            'article .published-date',
            'article .post-date',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                article_data["date"] = date_element.get('datetime') or date_element.get_text(strip=True)
                break
        
        # Extract content more efficiently
        article_section = soup.select_one('article')
        if article_section:
            # Remove unwanted elements in one go
            unwanted_selectors = [
                'script', 'style', 'h1', 'time', '.date', '.published-date', 
                '.post-date', '.ad', '.advertisement', '.related-articles', 
                '.comments', '.social-share', '.author-info', 'nav'
            ]
            
            for selector in unwanted_selectors:
                for element in article_section.select(selector):
                    element.decompose()
            
            # Get clean text content
            content_text = article_section.get_text(separator='\n', strip=True)
            
            # Clean up excessive whitespace and newlines
            lines = [line.strip() for line in content_text.split('\n') if line.strip()]
            article_data["content"] = '\n'.join(lines)
        
        return str(article_data)
    
    except Exception as e:
        return f"Error processing {url}: {str(e)}"


def get_news_data(urls: List[str], max_workers: int = 3) -> List[str]:
    """
    Process a list of URLs concurrently and return a list of scraped news results
    
    Args:
        urls (List[str]): List of URLs to scrape
        max_workers (int): Maximum number of concurrent threads (default: 3)
    
    Returns:
        List[str]: List of scraped article data as strings
    """
    if not urls:
        return []
    
    # Limit concurrent workers to avoid overwhelming the target server
    max_workers = min(max_workers, len(urls), 5)  # Cap at 5 to be respectful
    
    results = []
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(scrape_single_url, url): url for url in urls}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result(timeout=30)  # 30 second timeout per URL
                    results.append(result)
                except Exception as e:
                    results.append(f"Error processing {url}: {str(e)}")
    
    finally:
        # Clean up all thread-local drivers
        cleanup_driver()
    
    return results


def get_news_data_sequential(urls: List[str]) -> List[str]:
    """
    Sequential version for comparison or when concurrent processing is not desired
    """
    results = []
    driver = None
    
    # Set up a single driver for all URLs
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(3)
        driver.set_page_load_timeout(10)
        
        for url in urls:
            try:
                # Load the page
                driver.get(url)
                
                # Wait for article element
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'article'))
                )
                
                # Process with BeautifulSoup (same logic as concurrent version)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                article_data = {
                    "title": "",
                    "date": "",
                    "content": "",
                    "source_url": url
                }
                
                # Extract title
                title_selectors = ['article h1', 'h1.article-title', 'h1']
                for selector in title_selectors:
                    title_element = soup.select_one(selector)
                    if title_element:
                        article_data["title"] = title_element.get_text(strip=True)
                        break
                
                # Extract date
                date_selectors = [
                    'article time[datetime]', 'article .date', 'article .published-date',
                    'article .post-date', 'time[datetime]'
                ]
                
                for selector in date_selectors:
                    date_element = soup.select_one(selector)
                    if date_element:
                        article_data["date"] = date_element.get('datetime') or date_element.get_text(strip=True)
                        break
                
                # Extract content
                article_section = soup.select_one('article')
                if article_section:
                    unwanted_selectors = [
                        'script', 'style', 'h1', 'time', '.date', '.published-date', 
                        '.post-date', '.ad', '.advertisement', '.related-articles', 
                        '.comments', '.social-share', '.author-info', 'nav'
                    ]
                    
                    for selector in unwanted_selectors:
                        for element in article_section.select(selector):
                            element.decompose()
                    
                    content_text = article_section.get_text(separator='\n', strip=True)
                    lines = [line.strip() for line in content_text.split('\n') if line.strip()]
                    article_data["content"] = '\n'.join(lines)
                
                results.append(str(article_data))
                
            except Exception as e:
                results.append(f"Error processing {url}: {str(e)}")
    
    finally:
        if driver:
            driver.quit()
    
    return results


def main():
    """Test the article scraping functionality with sample blog URLs"""
    test_urls = [
        "https://wallstreetcn.com/articles/3747562",
        "https://wallstreetcn.com/articles/3747573",
        "https://wallstreetcn.com/articles/3747570"
    ]
    print(f"Testing concurrent article scraping for URLs: {test_urls}")
    
    # Test concurrent version
    start_time = time.time()
    articles_data = get_news_data(test_urls)
    end_time = time.time()
    
    print(f"Concurrent processing took {end_time - start_time:.2f} seconds")
    for data in articles_data:
        print(data[:200] + "..." if len(data) > 200 else data)


if __name__ == "__main__":
    main()
