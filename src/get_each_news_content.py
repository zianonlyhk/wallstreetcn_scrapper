from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time


def get_news_data(url: str):
    # Set up headless Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load the page
        driver.get(url)
        
        # Wait for the <article> element to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'article'))
        )
        time.sleep(5)  # Wait for content to load

        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Initialize data dictionary
        article_data = {
            "title": "",
            "date": "",
            "content": "",
            "source_url": url
        }
        
        # Extract title - common patterns for article titles
        title_element = soup.select_one('article h1') or soup.select_one('h1.article-title') or soup.select_one('h1')
        if title_element:
            article_data["title"] = title_element.text.strip()
        
        # Extract date - look for common date patterns
        # Try different common selectors for dates
        date_element = (
            soup.select_one('article time') or 
            soup.select_one('article .date') or 
            soup.select_one('article .published-date') or
            soup.select_one('article .post-date') or
            soup.select_one('time')
        )
        
        if date_element:
            if date_element.get('datetime'):
                article_data["date"] = date_element.get('datetime')
            else:
                article_data["date"] = date_element.text.strip()
        
        # Select the <article> section for content
        article_section = soup.select_one('article')
        if not article_section:
            print("No <article> section found on the page.")
            return article_data
        
        # Remove unwanted elements within the article
        for unwanted in article_section.select('script, style, article h1, article time, article .date, article .published-date, article .post-date, time, .ad, .advertisement, .related-articles, .comments'):
            unwanted.decompose()
        
        # Extract all visible text
        visible_text = []
        for element in article_section.find_all(text=True):
            text = element.strip()
            visible_text.append(text)
        
        # Join text with newlines, removing excessive empty lines
        content_text = '\n'.join(line for line in visible_text if line)
        
        # Remove the value before the first newline (and the newline itself)
        if '\n' in content_text:
            article_data["content"] = content_text.split('\n', 1)[1]
        else:
            article_data["content"] = content_text
        
        return str(article_data)
    
    except Exception as e:
        print(f"Error extracting article content: {e}")
        return {
            "title": "",
            "date": "",
            "content": f"Error: {str(e)}",
            "source_url": url
        }
    
    finally:
        driver.quit()


def main():
    """Test the article scraping functionality with a sample blog URL"""
    test_url = "https://wallstreetcn.com/articles/3745696"  # Replace with a real blog URL
    print(f"Testing article scraping for URL: {test_url}")
    
    article_data = get_news_data(test_url)
    print(article_data)


if __name__ == "__main__":
    main()
