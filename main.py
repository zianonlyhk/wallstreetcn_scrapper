from mcp.server.fastmcp import FastMCP
from src.get_news_list import get_news_entries_as_json
from src.get_each_news_content import get_news_data

mcp = FastMCP("lins_financial_news_crawler")


@mcp.tool()
def mcp_get_news_entries(time_filter: int=24) -> str:
    """
    使用 get_news_entries 函数获取新闻条目，并返回 JSON 字符串。

    Args:
        time_filter (int, 可选)：如果提供，仅返回在过去 'time_filter' 小时内发布的新闻条目。默认值为 24 小时。
    Returns:
        str：包含编号，标题，URL的新闻条目 JSON 字符串。
    """
    return get_news_entries_as_json(time_filter=time_filter)


@mcp.tool()
def mcp_get_each_news_content(url_to_be_scraped: str) -> str:
    """
    使用 mcp_get_each_news_content 函数从单一地址获取新闻内容，并返回对应的 JSON 字符串。

    Args:
        url_to_be_scraped (str)：提取内容的单一新闻目标地址。
    Returns:
        str：包含标题，日期，URL的单一新闻条目 JSON 字符串。
    """
    return get_news_data(url=url_to_be_scraped)


if __name__ == "__main__":
    mcp.run(transport="stdio")