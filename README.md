# WallStreetCN News Scraper

[![MIT License][license-shield]][license-url]

A Python scraper that integrates with MCP to extract and structure financial news articles from [华尔街见闻](https://wallstreetcn.com/news/global), including each of the news article's headline, content, and metadata.

## Features

- MCP integration
- Scrapes news article listings with a prescribed time range
- Extracts full article content
- Returns content in the format of JSON with metadata

## Prerequisites

Before you begin, ensure you have met the following requirements:
- [uv](https://github.com/astral-sh/uv) package manager
- [Cherry Studio](https://github.com/CherryHQ/cherry-studio) for faster setup (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/zianonlyhk/wallstreetcn_scrapper.git
cd wallstreetcn_scrapper
```

2. Install a Python virtual environment using uv: 
```bash
uv venv
```

3. Install dependencies using uv:
```bash
uv run pip install -e .
```

## Usage

### Standalone test instances

Run the scraper component directly:
```bash
uv run python src/get_news_list.py
```

or
```bash
uv run python src/get_news_content.py
```

### MCP Integration

The scraper provides two MCP tools:

1. Get news listings:
```python
@mcp.tool()
def mcp_get_news_entries(input_time_filter: int=24) -> str:
    """Returns comma-separated JSON of news entries from past X hours (default: 24)"""
```

2. Get news content:
```python
@mcp.tool()
def mcp_get_news_content(urls_to_be_scraped: list[str]) -> list[str]:
    """Returns a list of JSON objects for specified news URLs"""
```

### Using with Cherry Studio

Use the following as a reference when setting up the MCP configuration of Cherry Studio. Change the part of `/foo/bar` under `"args"` into the directory location containing this project source file. For example, to turn `/foo/bar/wallstreetcn_scrapper` into `/home/user/Downloads/wallstreetcn_scrapper`.
```
{
  "mcpServers": {
    "wallstreetcn_scrapper": {
      "name": "wallstreetcn_scrapper",
      "type": "stdio",
      "description": "帮您从wallstreetcn.com生成每日金融新闻稿。Copyright (c) Zian Huang 2025",
      "isActive": true,
      "registryUrl": "",
      "timeout": "180",
      "command": "uv",
      "args": [
        "--directory",
        "/foo/bar/wallstreetcn_scrapper",
        "run",
        "main.py"
      ]
    }
  }
}
```

## License

Distributed under the MIT License. See `LICENSE` for more information.

<!-- MARKDOWN LINKS & IMAGES -->
[license-shield]: https://img.shields.io/github/license/zianonlyhk/wallstreetcn_scrapper
[license-url]: https://github.com/zianonlyhk/wallstreetcn_scrapper/blob/main/LICENSE
