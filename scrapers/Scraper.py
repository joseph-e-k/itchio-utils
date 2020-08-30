import dataclasses
import functools
from collections import defaultdict
from datetime import datetime

import requests
from lxml import html

from GameInfo import ItchGamePageInfo

ITCH_WEB_ENCODING = "UTF-8"


def optional_call(func, arg):
    if arg is None:
        return None
    return func(arg)


class NodeWrapper:
    def __init__(self, node=None):
        self._node = node

    @property
    def text(self):
        for node in self._iter_nodes():
            if node.text:
                return node.text

        return str()

    def _iter_nodes(self):
        if self._node is None:
            return

        yield self._node
        yield from self._node

    def get_attribute(self, attribute, default=None):
        for node in self._iter_nodes():
            try:
                return node.attrib[attribute]
            except KeyError:
                continue
        return default

    def xpath(self, *args, **kwargs):
        if self._node is None:
            return [NodeWrapper()]
        return [NodeWrapper(node) for node in self._node.xpath(*args, **kwargs)]

    def __iter__(self):
        if self._node is None:
            return iter([])
        return iter(self._node)

    def __bool__(self):
        return self._node is not None


@dataclasses.dataclass(frozen=True)
class Scraper:
    username: str
    cookie: str

    @functools.lru_cache
    def get_page_html_tree(self, url):
        response = requests.request(
            method="GET",
            url=url,
            headers={
                "Cookie": self.cookie
            }
        )

        response.raise_for_status()

        return html.fromstring(response.content.decode(ITCH_WEB_ENCODING))

    def scrape_itch_game_page_info(self, url):
        try:
            page_tree = self.get_page_html_tree(url)
        except requests.HTTPError:
            return ItchGamePageInfo()

        try:
            custom_page_node = page_tree.xpath("//div[contains(@class, 'page_widget')]")[0]
            description_node = custom_page_node.xpath(".//div[contains(@class, 'formatted_description')]")[0]
        except IndexError:
            description = ""
        else:
            description = html.tostring(description_node, pretty_print=True, encoding="unicode")

        table_body_node = page_tree.xpath("//div[@class='game_info_panel_widget']/table/tbody")[0]
        nodes = defaultdict(NodeWrapper, {
            row_node.xpath("./td")[0].text: NodeWrapper(row_node.xpath("./td")[1])
            for row_node in table_body_node.xpath("./tr")
        })

        return ItchGamePageInfo(
            description=description,
            published_at=self._parse_datetime(nodes["Published"].get_attribute("title")),
            updated_at=self._parse_datetime(nodes["Updated"].get_attribute("title")),
            status=nodes["Status"].text,
            category=nodes["Category"].text,
            mean_rating=optional_call(float, nodes["Rating"].get_attribute("title")),
            number_of_ratings=optional_call(int, nodes["Rating"].xpath(".//span[@class='rating_count']")[0].get_attribute("content")),
            author_names=frozenset(child_node.text for child_node in (nodes["Authors"] or nodes["Author"])),
            author_urls=frozenset(child_node.attrib["href"] for child_node in (nodes["Authors"] or nodes["Author"])),
            genre=nodes["Genre"].text,
            tags=frozenset(child_node.text for child_node in nodes["Tags"]),
            links=frozenset((child_node.text, child_node.attrib.get("href")) for child_node in nodes["Links"])
        )

    @staticmethod
    def _parse_datetime(datetime_string):
        if datetime_string is None:
            return None

        return datetime.strptime(datetime_string, "%d %B %Y @ %H:%M")
