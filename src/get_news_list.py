from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time
import json
from urllib.parse import urljoin
from datetime import datetime, timedelta


def get_news_entries(url='https://wallstreetcn.com/news/global', time_filter=24):
    """
    从指定的 URL 获取新闻条目。
    
    Args:
        url (str, 可选)：要爬取的页面 URL。默认值为 'https://wallstreetcn.com/news/global'。
        time_filter (int, 可选)：如果提供，则仅返回在过去 'time_filter' 小时内发布的新闻条目。默认值为 24 小时。
    Returns:
        list：包含编号，标题，URL的新闻条目列表。
    """
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
        
        # Wait for news links to load (adjust selector based on page structure)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/articles/"]'))
        )

        # Scroll to load more content (handle infinite scroll)
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(time_filter//12 + 1):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Wait for content to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Extract news links
        news_pattern = r'^https://wallstreetcn\.com/articles/\d+$'
        news_entries = []
        
        # Calculate the cutoff time if time_filter is provided
        cutoff_time = None
        if time_filter is not None:
            # Use timezone-aware datetime to match the format from the webpage
            from datetime import timezone
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_filter)
        
        # Find all anchor tags
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            try:
                href = link.get_attribute('href')
                if href and re.match(news_pattern, urljoin(url, href)):
                    # If time_filter is provided, check the publication time
                    if time_filter is not None:
                        # Find the time element associated with this link based on the specific structure
                        # Based on the observed XPath structure, the time element is in a sibling div
                        time_element = None
                        try:
                            # Get the parent div of the link
                            parent_div = link.find_element(By.XPATH, './ancestor::div[1]')
                            
                            # Look for time element in the parent div's children
                            # First try to find a direct time element
                            try:
                                time_element = parent_div.find_element(By.XPATH, './/time')
                            except:
                                # If no direct time element, look for elements with time-related classes
                                try:
                                    time_element = parent_div.find_element(By.XPATH, './/*[contains(@class, "time") or contains(@class, "date")]')
                                except:
                                    # If still not found, try looking in sibling divs
                                    try:
                                        # Get the grandparent that contains both the link div and time div
                                        grandparent = parent_div.find_element(By.XPATH, './parent::*')
                                        # Look for time elements in other child divs
                                        time_element = grandparent.find_element(By.XPATH, './/div[2]//time | .//div[contains(@class, "time") or contains(@class, "date")]')
                                    except:
                                        pass
                            
                            # If still no time element, check text content for time patterns
                            if not time_element:
                                try:
                                    # Check the parent div's text for time patterns
                                    text_content = parent_div.text
                                    if re.search(r'\d+\s+(minute|hour|day|week)s?\s+ago|today at', text_content, re.IGNORECASE):
                                        time_element = parent_div
                                except:
                                    pass
                        except Exception as e:
                            print(f"Error finding time element: {e}")
                        
                        # If we found a time element, check if it's within our time filter
                        if time_element:
                            # Extract the datetime directly from the datetime attribute
                            try:
                                # Get the datetime attribute from the time element
                                datetime_attr = time_element.get_attribute('datetime')
                                if datetime_attr:
                                    # Parse the ISO format datetime
                                    # Example format: "2025-04-22T21:22:54.000+08:00"
                                    post_time = datetime.fromisoformat(datetime_attr)
                                    
                                    # If we could parse the time and it's older than our cutoff, skip this link
                                    if post_time and cutoff_time:
                                        # Convert post_time to UTC for consistent comparison
                                        from datetime import timezone
                                        post_time_utc = post_time.astimezone(timezone.utc)
                                        if post_time_utc < cutoff_time:
                                            continue
                                else:
                                    # Fallback if datetime attribute is not available
                                    print(f"No datetime attribute found for time element: {time_element.text}")
                            except Exception as e:
                                print(f"Error parsing datetime: {e}")
                    
                    # If we passed the time filter check or no time filter was specified
                    full_url = urljoin(url, href)
                    
                    # Extract the title from the link text or from a child element
                    title = ""
                    try:
                        # First try to get the text directly from the link
                        title = link.text.strip()
                        
                        # If the link text is empty, try to find a title element within the link
                        if not title:
                            title_element = link.find_element(By.XPATH, './/*[contains(@class, "title") or self::h1 or self::h2 or self::h3 or self::h4]')
                            title = title_element.text.strip()
                            
                        # If still no title, try to find any text content in the link
                        if not title:
                            title = link.get_attribute('textContent').strip()
                            
                        # If still no title, use the URL as a fallback
                        if not title:
                            title = "Article " + href.split('/')[-1]
                    except Exception as e:
                        print(f"Error extracting title: {e}")
                        title = "Article " + href.split('/')[-1]  # Use article ID as fallback title
                    
                    # Add the entry to our list with an ID based on the current position
                    news_entries.append({
                        # ID starts at 1 rather than 0
                        "ID": len(news_entries)+1,
                        "Title": title,
                        "URL": full_url
                    })
            except Exception as e:
                # Print the specific error for debugging
                print(f"Error processing link: {e}")
                continue
        
        # Print or process the collected entries
        for entry in news_entries:
            print(f"ID: {entry['ID']}, Title: {entry['Title']}, URL: {entry['URL']}")
        
        return news_entries
    
    except Exception as e:
        print(f"Error crawling the page: {e}")
        return []
    
    finally:
        driver.quit()


# news_entries is a list of python dict(s). wrap it in braces to have a JSON file
def wrap_in_braces(s):
    if not s:  # Handle empty string
        return "{}"
    return "{" + s[1:-1] + "}" if len(s) > 1 else "{}}"


def get_news_entries_as_json(url='https://wallstreetcn.com/news/global', time_filter=24, indent=0):
    """
    从指定的 URL 获取新闻条目，并返回 JSON 字符串。
    
    Args:
        url (str, 可选)：要爬取的页面 URL。默认值为 'https://wallstreetcn.com/news/global'。
        time_filter (int, 可选)：如果提供，则仅返回在过去 'time_filter' 小时内发布的新闻条目。默认值为 24 小时。
        indent (int, 可选)：JSON 字符串的缩进。默认值为 0。
    Returns:
        str：包含编号，标题，URL的新闻条目 JSON 字符串。
    """
    print(f"Crawling news entries from {url}")
    news_entries = get_news_entries(url, time_filter)

    return wrap_in_braces(json.dumps(news_entries, indent=indent, ensure_ascii=False))


if __name__ == "__main__":
    json_str = get_news_entries_as_json(time_filter=2)
    print(json_str)

