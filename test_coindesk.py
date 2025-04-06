"""
Module tests for CoindeskSpider functionality.
Uses helper methods to generate common HTML snippets and centralizes date/time handling.
"""

import unittest
import textwrap
from datetime import datetime
from scrapy.http import TextResponse
from parsel import Selector

from coindesk import CoindeskSpider
from parsel import Selector, SelectorList

class FakeArticle:
    """
    A helper class to simulate an article element for testing.
    """
    def __init__(self, html: str) -> None:
        """
        Initializes the FakeArticle with HTML content.

        Args:
            html (str): The HTML string representing the article.

        Raises:
            ValueError: If the provided HTML string is empty.
        """
        if not html:
            raise ValueError("HTML content cannot be empty.")
        self.selector: Selector = Selector(text=html)

    def xpath(self, query: str, **kwargs) -> SelectorList:
        """
        Run an XPath query on the article's HTML content.

        Args:
            query (str): An XPath expression.
            **kwargs: Additional keyword arguments for the XPath query.

        Returns:
            SelectorList: The list of selectors matching the XPath query.

        Raises:
            ValueError: If the provided query is empty or consists only of whitespace.
        """
        if not query or not query.strip():
            raise ValueError("XPath query must be a non-empty string.")

        return self.selector.xpath(query, **kwargs)

class TestCoindeskSpider(unittest.TestCase):
    def setUp(self) -> None:
        """Initialize a fresh instance of CoindeskSpider for each test case."""
        self.spider: CoindeskSpider = CoindeskSpider()

    def generate_article_html(self, *, include_time=True,
                              time_value="2023-10-10T12:34:56Z",
                              title="Test Article",
                              link="http://example.com/article",
                              author="John Doe",
                              paragraphs=None):
        """
        Generates HTML for a single article using provided values.
        """
        if paragraphs is None:
            paragraphs = ["Paragraph one.", "Paragraph two."]
        time_html = f'<time datetime="{time_value}"></time>' if include_time else ""
        paragraphs_html = "\n".join(f"<p>{p}</p>" for p in paragraphs)
        html = f"""
            <article>
                {time_html}
                <h4>{title.strip()}</h4>
                <a href="{link}"></a>
                <span class="author">{author}</span>
                {paragraphs_html}
            </article>
        """
        return textwrap.dedent(html).strip()

    def get_today_date(self) -> str:
        """
        Returns today's date in ISO format (YYYY-MM-DD).
        Uses the local timezone.

        Returns:
            str: Today's date in ISO format.
        """
        today = datetime.now().date()
        return today.isoformat()

    def test_extract_article_valid(self):
        """Test extraction of a valid article with all required fields."""
        html = self.generate_article_html(
            include_time=True,
            time_value="2023-10-10T12:34:56Z",
            title="Test Article",
            link="http://example.com/article",
            author="John Doe",
            paragraphs=["Paragraph one.", "Paragraph two."]
        )
        fake_article = FakeArticle(html)
        item = self.spider.extract_article(fake_article)
        self.assertIsNotNone(item, "Expected a valid item to be extracted")

        expected_fields = {
            "title": "Test Article",
            "link": "http://example.com/article",
            "author": "John Doe",
        }
        for field, expected_value in expected_fields.items():
            with self.subTest(field=field):
                self.assertEqual(item.get(field), expected_value)

        with self.subTest(field="body"):
            body = item.get("body")
            self.assertIsInstance(body, str, "Body should be a string")
            self.assertIn("Paragraph one.", body)

        with self.subTest(field="hour"):
            self.assertEqual(item.get("hour"), "12:34:56", "Hour should match the extracted time segment")

        with self.subTest(field="published_at"):
            published_at = item.get("published_at")
            self.assertIsInstance(published_at, str, "Published_at must be a string")
            self.assertTrue(published_at.startswith("2023-10-10"), "Published date must start with '2023-10-10'")

    def test_extract_article_without_time(self):
        """Verify that extraction returns None if the time element is missing."""
        article_html = self.generate_article_html(
            include_time=False,
            title="Article Without Time",
            link="http://example.com/article",
            author="John Doe",
            paragraphs=["Content here."]
        )
        fake_article = FakeArticle(article_html)
        extracted_item = self.spider.extract_article(fake_article)
        self.assertIsNone(
            extracted_item,
            msg="Extraction should return None when the time element is not present."
        )

    def test_parse_filters_old_articles(self):
        """Test that the parse method filters out articles older than today."""
        today_iso = self.get_today_date()
        # Define time values: one for today's article and one far in the past.
        current_time = f"{today_iso}T08:00:00Z"
        old_time = "2000-01-01T00:00:00Z"

        # Generate HTML for a current article.
        article_today = self.generate_article_html(
            include_time=True,
            time_value=current_time,
            title="Today Article",
            link="http://example.com/today",
            author="Alice",
            paragraphs=["Today content."]
        )
        # Generate HTML for an old article.
        article_old = self.generate_article_html(
            include_time=True,
            time_value=old_time,
            title="Old Article",
            link="http://example.com/old",
            author="Bob",
            paragraphs=["Old content."]
        )
        # Combine both articles into one HTML document.
        html_content = f"""
            <html>
                <body>
                    {article_today}
                    {article_old}
                </body>
            </html>
        """
        dedented_html = textwrap.dedent(html_content).strip()
        response = TextResponse(url="http://example.com", body=dedented_html, encoding="utf-8")

        # Parse the response and verify only the current article is returned.
        articles = list(self.spider.parse(response))
        self.assertEqual(len(articles), 1, "Expected exactly one article to be extracted")
        self.assertEqual(articles[0].get("title"), "Today Article", "Extracted article title does not match")

if __name__ == '__main__':
    unittest.main(verbosity=2)
