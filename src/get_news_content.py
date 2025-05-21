import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional
from src.cache_utils import shared_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_page(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch page content with caching"""
    cached_content = shared_cache.get(url)
    if cached_content is not None:
        return cached_content
        
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                shared_cache.set(url, content)
                return content
            logger.warning(f"Failed to fetch {url}: Status {response.status}")
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
    return None

async def get_news_data(urls: list[str]) -> list[Dict]:
    """Process a list of URLs and return structured news data"""
    connector = aiohttp.TCPConnector(limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [fetch_page(session, url) for url in urls]
        pages = await asyncio.gather(*tasks)
        
        results = []
        for i, page in enumerate(pages):
            if not page:
                results.append({
                    "error": f"Failed to fetch {urls[i]}",
                    "source_url": urls[i]
                })
                continue
                
            try:
                soup = BeautifulSoup(page, 'html.parser')
                article_section = soup.select_one('article')
                if article_section:
                    article_data = process_article(soup, article_section, urls[i])
                    results.append(article_data)
                else:
                    results.append({
                        "error": f"No article content found at {urls[i]}",
                        "source_url": urls[i]
                    })
            except Exception as e:
                logger.error(f"Error processing {urls[i]}: {str(e)}")
                results.append({
                    "error": str(e),
                    "source_url": urls[i]
                })
    
    return results

def process_article(soup: BeautifulSoup, article_section, url: str) -> dict:
    """Process article content and return structured data"""
    article_data = {
        "title": "",
        "date": "",
        "content": "",
        "source_url": url
    }
    
    # Extract title
    title_element = soup.select_one('article h1') or soup.select_one('h1.article-title') or soup.select_one('h1')
    if title_element:
        article_data["title"] = title_element.text.strip()
    
    # Extract date
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
    
    # Remove unwanted elements
    for unwanted in article_section.select('script, style, article h1, article time, article .date, article .published-date, article .post-date, time, .ad, .advertisement, .related-articles, .comments'):
        unwanted.decompose()
    
    # Extract all visible text
    visible_text = []
    for element in article_section.find_all(string=True):
        text = element.strip()
        visible_text.append(text)
    
    # Join text with newlines
    content_text = '\n'.join(line for line in visible_text if line)
    
    if '\n' in content_text:
        article_data["content"] = content_text.split('\n', 1)[1]
    else:
        article_data["content"] = content_text
    
    return article_data


def main():
    """Test the article scraping functionality with sample blog URLs"""
    test_urls =[
        "https://wallstreetcn.com/articles/3747562",
        "https://wallstreetcn.com/articles/3747573",
        "https://wallstreetcn.com/articles/3747570"
    ]
    print(f"Testing article scraping for URLs: {test_urls}")
    
    articles_data = asyncio.run(get_news_data(test_urls))
    for data in articles_data:
        print(data)


if __name__ == "__main__":
    main()
