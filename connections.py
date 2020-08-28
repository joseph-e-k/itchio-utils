import dataclasses
import functools
import re

import requests
from lxml import html

from GameInfo import GameInfo

LOGIN_URL = "https://itch.io/login"
ITCH_WEB_ENCODING = "UTF-8"
BUNDLE_PAGE_URL_FORMAT = "https://itch.io/bundle/download/{}?page={}"


@dataclasses.dataclass(frozen=True)
class Connection:
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
        return html.fromstring(response.content.decode(ITCH_WEB_ENCODING))

    def get_bundle(self, bundle_slug):
        return BundleConnection(slug=bundle_slug, **dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class BundleConnection(Connection):
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
        games = []

        for game_row in game_rows:
            games.append(self.bundle_entry_html_to_game_info(game_row))

        return games

    @staticmethod
    def bundle_entry_html_to_game_info(html_tree):
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

        return GameInfo(
            title=title_node.text,
            url=title_node.attrib['href'],
            summary=summary_node.text,
            file_count=file_count,
            operating_systems=operating_systems
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

    return Connection(username, cookie)
