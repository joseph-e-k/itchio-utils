import dataclasses
import functools
import re
from collections import defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests
from lxml import html

from GameInfo import GameInfo, ItchMetadataBlock

LOGIN_URL = "https://itch.io/login"
ITCH_WEB_ENCODING = "UTF-8"
BUNDLE_PAGE_URL_FORMAT = "https://itch.io/bundle/download/{}?page={}"


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

    def scrape_itch_metadata_block(self, url):
        try:
            page_tree = self.get_page_html_tree(url)
        except requests.HTTPError:
            return ItchMetadataBlock()

        try:
            table_body_node = page_tree.xpath("//div[@class='game_info_panel_widget']/table/tbody")[0]
        except IndexError:
            print(f"No metadata block found at {url}")
            raise

        nodes = defaultdict(NodeWrapper, {
            row_node.xpath("./td")[0].text: NodeWrapper(row_node.xpath("./td")[1])
            for row_node in table_body_node.xpath("./tr")
        })

        return ItchMetadataBlock(
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

    def get_bundle(self, bundle_slug):
        return BundleScraper(slug=bundle_slug, **dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class BundleScraper(Scraper):
    slug: str

    def get_bundle_page_count(self):
        first_page_html_tree = self.get_bundle_page_html_tree(1)
        page_count_node = first_page_html_tree.xpath("//span[@class='pager_label']/a")[0]
        return int(page_count_node.text)

    def scrape_bundle_page(self, page_number):
        page_html_tree = self.get_bundle_page_html_tree(page_number)
        return self.parse_bundle_page(page_html_tree)

    def get_bundle_page_html_tree(self, page_number):
        return self.get_page_html_tree(BUNDLE_PAGE_URL_FORMAT.format(self.slug, page_number))

    def parse_bundle_page(self, html_tree):
        game_rows = html_tree.xpath("//div[@class='game_row']")

        with ThreadPoolExecutor() as executor:
            games = executor.map(self.bundle_entry_html_to_game_info, game_rows, timeout=60)

        return list(games)

    def bundle_entry_html_to_game_info(self, html_tree):
        title_node = html_tree.xpath(".//h2[@class='game_title']/a")[0]
        summary_node = html_tree.xpath(".//div[@class='meta_row game_short_text']")[0]
        try:
            file_count_node = html_tree.xpath(".//div[@class='meta_row file_count']")[0]
        except IndexError:
            file_count_node = None

        operating_systems = set()
        operating_system_nodes = html_tree.xpath(
            ".//div[@class='meta_row']/span[contains(@title, 'Available for ')]"
        )
        for node in operating_system_nodes:
            operating_systems.add(re.match(r"Available for (\w+)", node.attrib["title"]).group(1))

        if file_count_node is None:
            file_count = 1
        else:
            file_count = int(re.match(r"(\d+) files?", file_count_node.text).group(1))

        url = title_node.attrib['href']
        if re.match(r".*/.*/download/[a-zA-Z0-9_]+", url):
            url = "/".join(url.split("/")[:-2])

        itch_metadata_block = self.scrape_itch_metadata_block(url)

        return GameInfo(
            title=title_node.text,
            url=url,
            summary=summary_node.text,
            file_count=file_count,
            operating_systems=operating_systems,
            **dataclasses.asdict(itch_metadata_block)
        )


def connect(username, password):
    page_response = requests.get(LOGIN_URL)
    page_html_tree = html.fromstring(page_response.content)
    csrf_token_node = page_html_tree.xpath(".//input[@name='csrf_token']")[0]
    csrf_token = csrf_token_node.attrib["value"]
    itchio_token = re.search(r"\bitchio_token=([a-zA-Z0-9%]+);", page_response.headers["Set-Cookie"]).group(1)

    login_response = requests.post(
        LOGIN_URL,
        data=dict(
            username=username,
            password=password,
            csrf_token=csrf_token,
        ),
        headers={
            "Cookie": f"itchio_token={itchio_token}",
        }
    )

    login_response_cookies = login_response.headers["Set-Cookie"]
    login_token = re.search(r"\bitchio=([a-zA-Z0-9%]+);", login_response_cookies).group(1)
    cookie = f"itchio_token={itchio_token}; itchio={login_token}"

    return Scraper(username, cookie)
