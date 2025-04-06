from datetime import datetime
from typing import Optional, Generator

import scrapy
from typing import Optional

def parse_iso_datetime(dt_str: str) -> Optional[datetime]:
    """
    Parse an ISO formatted datetime string, handling the 'Z' timezone suffix.

    Args:
        dt_str (str): A datetime string in ISO 8601 format.

    Returns:
        Optional[datetime]: A datetime object if parsing succeeds; otherwise, None.
    """
    try:
        # Replace 'Z' with '+00:00' to comply with ISO 8601 format.
        iso_dt = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(iso_dt)
    except ValueError:
        # Optionally, integrate logging here to capture parsing errors.
        return None

class ArticleItem(scrapy.Item):
    """
    Represents an article scraped from Coindesk.

    Fields:
        title (str): The article's title.
        hour (str): Publication time in HH:MM:SS format.
        link (str): The article URL.
        author (str): The article's author.
        body (str): A short excerpt from the article.
        published_at (str): The publication datetime in ISO 8601 format.
    """
    title = scrapy.Field()
    hour = scrapy.Field()
    link = scrapy.Field()
    author = scrapy.Field()
    body = scrapy.Field()
    published_at = scrapy.Field()

class CoindeskSpider(scrapy.Spider):
    # Spider configuration
    name: str = "coindesk"
    allowed_domains: list[str] = ["coindesk.com"]
    start_urls: list[str] = ["https://www.coindesk.com/tag/bitcoin/"]
    custom_settings: dict[str, str] = {
        "USER_AGENT": "Mozilla/5.0 (compatible; CoindeskSpider/1.0; +https://www.coindesk.com/)"
    }

    def parse(self, response: scrapy.http.Response) -> Generator[ArticleItem, None, None]:
        """
        Parse the articles and yield ArticleItem objects for those published today.

        The method extracts articles from the response, validates required fields,
        and then yields only the articles with a publication date matching today's date.
        """
        today = datetime.now().date()

        for article in response.xpath("//article"):
            item = self.extract_article(article)
            if not item:
                self.logger.warning("Article extraction failed: missing required fields.")
                continue

            published_at = item.get("published_at")
            if not published_at:
                self.logger.error("Article missing 'published_at' field.")
                continue

            parsed_dt = parse_iso_datetime(published_at)
            if not parsed_dt:
                self.logger.error(
                    f"Failed to parse 'published_at' ({published_at}) for article titled '{item.get('title')}'."
                )
                continue

            if parsed_dt.date() == today:
                yield item

    def extract_article(self, article) -> Optional[ArticleItem]:
        """
        Extract and return an ArticleItem from an article element.
        Returns None if required fields are missing or datetime parsing fails.
        """
        # Extract and validate the datetime attribute.
        datetime_str = article.xpath(".//time/@datetime").get()
        if not datetime_str:
            self.logger.warning("Missing time attribute in article.")
            return None

        published_datetime = parse_iso_datetime(datetime_str)
        if not published_datetime:
            self.logger.error(f"Failed to parse datetime '{datetime_str}' in article.")
            return None

        # Extract and clean the title.
        title = article.xpath(".//h4//text()").get(default="").strip()
        if not title:
            self.logger.warning("Missing title in article.")
            return None

        # Extract remaining fields with defaults if necessary.
        link = article.xpath(".//a/@href").get()
        author = article.xpath(".//span[contains(@class, 'author')]/text()").get(default="Unknown").strip()
        body_texts = [txt.strip() for txt in article.xpath(".//p//text()").getall() if txt.strip()]
        body = " ".join(body_texts)

        return ArticleItem(
            title=title,
            hour=published_datetime.strftime("%H:%M:%S"),
            link=link,
            author=author,
            body=body,
            published_at=published_datetime.isoformat()
        )