import dataclasses
import functools
from datetime import datetime

from lxml import html

from decorators import aggregator
from records.GameInfo import ItchGamePageInfo
from records.build_record import RecordBuilder, field_builder
from scrapers.Scraper import Scraper


def optional_call(func, arg):
    if arg is None:
        return None
    return func(arg)


@dataclasses.dataclass(frozen=True)
class GamePageScraper(Scraper, RecordBuilder):
    root_node: html.HtmlEntity

    @field_builder(ItchGamePageInfo.description)
    def get_description(self):
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

    def get_simple_row_node(self, row_name):
        try:
            return self.table_nodes[row_name].xpath("./*")[0]
        except (KeyError, IndexError):
            return None

    def get_simple_row_attribute(self, row_name, attribute_name):
        node = self.get_simple_row_node(row_name)
        if node is None:
            return None
        return node.attrib[attribute_name]

    def get_simple_row_text(self, row_name):
        node = self.get_simple_row_node(row_name)
        if node is None:
            return None
        return node.text

    @field_builder(ItchGamePageInfo.published_at)
    def get_publication_date(self):
        return self._parse_datetime(self.get_simple_row_attribute("Published", "title"))

    @field_builder(ItchGamePageInfo.updated_at)
    def get_update_date(self):
        return self._parse_datetime(self.get_simple_row_attribute("Updated", "title"))

    @field_builder(ItchGamePageInfo.status)
    def get_status(self):
        return self.get_simple_row_text("Status")

    @field_builder(ItchGamePageInfo.category)
    def get_category(self):
        return self.get_simple_row_text("Category")

    @field_builder(ItchGamePageInfo.mean_rating)
    def get_mean_rating(self):
        return optional_call(float, self.get_simple_row_attribute("Rating", "title"))

    @field_builder(ItchGamePageInfo.number_of_ratings)
    def get_number_of_ratings(self):
        try:
            count_str = self.table_nodes["Rating"].xpath("./*/span[@class='rating_count']")[0].attrib["content"]
        except (KeyError, IndexError):
            return None
        return int(count_str)

    @functools.cached_property
    @aggregator(tuple)
    def author_nodes(self):
        parent_node = self.table_nodes.get("Authors")
        if parent_node is None:
            parent_node = self.table_nodes.get("Author")
        if parent_node is None:
            return

        yield from parent_node

    @field_builder(ItchGamePageInfo.author_names)
    @aggregator(tuple)
    def get_author_names(self):
        for author_node in self.author_nodes:
            yield author_node.text

    @field_builder(ItchGamePageInfo.author_names)
    @aggregator(tuple)
    def get_author_names(self):
        for author_node in self.author_nodes:
            yield author_node.attrib["href"]

    @field_builder(ItchGamePageInfo.genre)
    def get_genre(self):
        return self.get_simple_row_text("Genre")

    @field_builder(ItchGamePageInfo.tags)
    @aggregator(frozenset)
    def get_tags(self):
        for child_node in self.table_nodes.get("Tags", []):
            yield child_node.text

    @field_builder(ItchGamePageInfo.links)
    @aggregator(frozenset)
    def get_links(self):
        for child_node in self.table_nodes.get("Links", []):
            yield child_node.text, child_node.attrib["href"]

    @staticmethod
    def _parse_datetime(datetime_string):
        if datetime_string is None:
            return None

        return datetime.strptime(datetime_string, "%d %B %Y @ %H:%M")
