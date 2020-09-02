import dataclasses
import functools
from datetime import datetime

from lxml import html

from decorators import aggregator
from records.GameInfo import ItchGamePageInfo
from scrapers.Scraper import Scraper


def optional_call(func, arg):
    if arg is None:
        return None
    return func(arg)


@dataclasses.dataclass(frozen=True)
class GamePageScraper(Scraper):
    root_node: html.HtmlEntity

    def get_game_page_info(self):
        return ItchGamePageInfo(
            description=self._get_description(),
            published_at=self._get_publication_date(),
            updated_at=self._get_update_date(),
            status=self._get_status(),
            category=self._get_category(),
            mean_rating=self._get_mean_rating(),
            number_of_ratings=self._get_number_of_ratings(),
            author_names=self._get_author_names(),
            author_urls=self._get_author_urls(),
            genre=self._get_genre(),
            tags=self._get_tags(),
            links=self._get_links()
        )

    def _get_description(self):
        try:
            custom_page_node = self.root_node.xpath("//div[contains(@class, 'page_widget')]")[0]
            description_node = custom_page_node.xpath(".//div[contains(@class, 'formatted_description')]")[0]
        except IndexError:
            return ""
        return html.tostring(description_node, pretty_print=True, encoding="unicode")

    @functools.cached_property
    def table_nodes(self):
        table_body_node = self.root_node.xpath("//div[@class='game_info_panel_widget']/table/tbody")[0]
        return {
            row_node.xpath("./td")[0].text: row_node.xpath("./td")[1]
            for row_node in table_body_node.xpath("./tr")
        }

    def _get_simple_row_node(self, row_name):
        try:
            return self.table_nodes[row_name].xpath("./*")[0]
        except (KeyError, IndexError):
            return None

    def _get_simple_row_attribute(self, row_name, attribute_name):
        node = self._get_simple_row_node(row_name)
        if node is None:
            return None
        return node.attrib[attribute_name]

    def _get_simple_row_text(self, row_name):
        node = self._get_simple_row_node(row_name)
        if node is None:
            return None
        return node.text

    def _get_publication_date(self):
        return self._parse_datetime(self._get_simple_row_attribute("Published", "title"))

    def _get_update_date(self):
        return self._parse_datetime(self._get_simple_row_attribute("Updated", "title"))

    def _get_status(self):
        return self._get_simple_row_text("Status")

    def _get_category(self):
        return self._get_simple_row_text("Category")

    def _get_mean_rating(self):
        return optional_call(float, self._get_simple_row_attribute("Rating", "title"))

    def _get_number_of_ratings(self):
        try:
            count_str = self.table_nodes["Rating"].xpath("./*/span[@class='rating_count']")[0].attrib["content"]
        except (KeyError, IndexError):
            return None
        return int(count_str)

    @functools.cached_property
    @aggregator(tuple)
    def _author_nodes(self):
        parent_node = self.table_nodes.get("Authors")
        if parent_node is None:
            parent_node = self.table_nodes.get("Author")
        if parent_node is None:
            return

        yield from parent_node

    @aggregator(tuple)
    def _get_author_names(self):
        for author_node in self._author_nodes:
            yield author_node.text

    @aggregator(tuple)
    def _get_author_urls(self):
        for author_node in self._author_nodes:
            yield author_node.attrib["href"]

    def _get_genre(self):
        return self._get_simple_row_text("Genre")

    @aggregator(frozenset)
    def _get_tags(self):
        for child_node in self.table_nodes.get("Tags", []):
            yield child_node.text

    @aggregator(frozenset)
    def _get_links(self):
        for child_node in self.table_nodes.get("Links", []):
            yield child_node.text, child_node.attrib["href"]

    @staticmethod
    def _parse_datetime(datetime_string):
        if datetime_string is None:
            return None

        return datetime.strptime(datetime_string, "%d %B %Y @ %H:%M")
