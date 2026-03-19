from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_scrape_page_returns_content():
    from research_graph.tools.scraper import scrape_page

    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.content = AsyncMock(return_value="<html><body>Hello World</body></html>")
    mock_page.inner_text = AsyncMock(return_value="Hello World")

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    with patch("research_graph.tools.scraper._get_browser", return_value=mock_browser):
        result = await scrape_page("https://example.com")
    assert "Hello World" in result


@pytest.mark.asyncio
async def test_scrape_page_handles_error():
    from research_graph.tools.scraper import scrape_page

    with patch("research_graph.tools.scraper._get_browser", side_effect=Exception("fail")):
        result = await scrape_page("https://example.com")
    assert "Error scraping" in result
