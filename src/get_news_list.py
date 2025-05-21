import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
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

async def get_news_entries(url='https://wallstreetcn.com/news/global', time_filter=24):
    """
    从指定的 URL 获取新闻条目。
    
    Args:
        url (str, 可选)：要爬取的页面 URL。默认值为 'https://wallstreetcn.com/news/global'。
        time_filter (int, 可选)：如果提供，则仅返回在过去 'time_filter' 小时内发布的新闻条目。默认值为 24 小时。
    Returns:
        list：包含编号，标题，URL的新闻条目列表。
    """
    connector = aiohttp.TCPConnector(limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        try:
            content = await fetch_page(session, url)
            if not content:
                return []
                
            soup = BeautifulSoup(content, 'html.parser')
            news_entries = []
            news_pattern = r'^https://wallstreetcn\.com/articles/\d+$'
            
            # Calculate cutoff time if filtering by time
            cutoff_time = None
            if time_filter is not None:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_filter)
            
            # Find all article links
            article_links = soup.select('a[href*="/articles/"]')
            for link in article_links:
                try:
                    href = link.get('href')
                    if not href or not re.match(news_pattern, urljoin(url, href)):
                        continue
                        
                    full_url = urljoin(url, href)
                    
                    # Extract title
                    title = link.text.strip()
                    if not title:
                        title_element = link.select_one('.title, h1, h2, h3, h4')
                        if title_element:
                            title = title_element.text.strip()
                    
                    # Extract time if filtering
                    if time_filter is not None:
                        time_element = link.find_parent().select_one('time, .time, .date')
                        if time_element:
                            datetime_str = time_element.get('datetime') or time_element.text.strip()
                            try:
                                post_time = datetime.fromisoformat(datetime_str).astimezone(timezone.utc)
                                if post_time < cutoff_time:
                                    continue
                            except ValueError:
                                logger.warning(f"Could not parse datetime: {datetime_str}")
                    
                    news_entries.append({
                        "ID": len(news_entries) + 1,
                        "Title": title or f"Article {href.split('/')[-1]}",
                        "URL": full_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing link: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_entries)} news entries")
            return news_entries
            
        except Exception as e:
            logger.error(f"Error crawling page: {str(e)}")
            return []


async def main():
    """Main async entry point"""
    try:
        news_entry_list = await get_news_entries(url='https://wallstreetcn.com/news/global', time_filter=24)
        print(news_entry_list)
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        return "{}"


if __name__ == "__main__":
    asyncio.run(main())
