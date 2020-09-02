import dataclasses
import functools
import re

import requests
from lxml import html

from records.GameInfo import GameInfo, ItchGamePageInfo
from decorators import aggregator
from scrapers.GamePageScraper import GamePageScraper
from scrapers.Scraper import Scraper


@dataclasses.dataclass(frozen=True)
class BundleEntryScraper(Scraper):
    root_node: html.HtmlElement

    def get_game_info(self):
        return GameInfo(
            title=self._get_title(),
            summary=self._get_summary(),
            url=self._get_url(),
            operating_systems=self._get_operating_systems(),
            file_count=self._get_file_count(),
            details=self._get_details()
        )

    @functools.lru_cache
    def _get_title_node(self):
        return self.root_node.xpath(".//h2[@class='game_title']/a")[0]

    def _get_title(self):
        return self._get_title_node().text

    def _get_summary(self):
        return self.root_node.xpath(".//div[@class='meta_row game_short_text']")[0].text

    def _get_file_count(self):
        try:
            file_count_node = self.root_node.xpath(".//div[@class='meta_row file_count']")[0]
        except IndexError:
            return 1
        else:
            return int(re.match(r"(\d+) files?", file_count_node.text).group(1))

    @aggregator(frozenset)
    def _get_operating_systems(self):
        operating_system_nodes = self.root_node.xpath(
            ".//div[@class='meta_row']/span[contains(@title, 'Available for ')]"
        )
        for node in operating_system_nodes:
            yield re.match(r"Available for (\w+)", node.attrib["title"]).group(1)

    @functools.lru_cache
    def _get_url(self):
        url = self._get_title_node().attrib['href']
        if re.match(r".*/.*/download/[a-zA-Z0-9_]+", url):
            return "/".join(url.split("/")[:-2])
        return url

    def _get_details(self):
        try:
            page_tree = self.get_page_html_tree(self._get_url())
        except requests.HTTPError:
            return ItchGamePageInfo()
        return GamePageScraper(self.cookie, page_tree).get_game_page_info()
