import dataclasses
import functools
import re
from datetime import datetime

import requests
from lxml import html

from records.GameInfo import GameInfo, ItchGamePageInfo
from decorators import aggregator
from records.build_record import RecordBuilder, field_builder
from scrapers.GamePageScraper import GamePageScraper
from scrapers.Scraper import Scraper


@dataclasses.dataclass(frozen=True)
class BundleEntryScraper(Scraper, RecordBuilder):
    root_node: html.HtmlElement

    @functools.lru_cache
    def _get_title_node(self):
        return self.root_node.xpath(".//h2[@class='game_title']/a")[0]

    @field_builder(GameInfo.title)
    def _get_title(self):
        return self._get_title_node().text

    @field_builder(GameInfo.summary)
    def _get_summary(self):
        return self.root_node.xpath(".//div[@class='meta_row game_short_text']")[0].text

    @field_builder(GameInfo.file_count)
    def _get_file_count(self):
        try:
            file_count_node = self.root_node.xpath(".//div[@class='meta_row file_count']")[0]
        except IndexError:
            return 1
        else:
            return int(re.match(r"(\d+) files?", file_count_node.text).group(1))

    @field_builder(GameInfo.operating_systems)
    @aggregator(frozenset)
    def _get_operating_systems(self):
        operating_system_nodes = self.root_node.xpath(
            ".//div[@class='meta_row']/span[contains(@title, 'Available for ')]"
        )
        for node in operating_system_nodes:
            yield re.match(r"Available for (\w+)", node.attrib["title"]).group(1)

    @field_builder(GameInfo.url)
    @functools.lru_cache
    def _get_url(self):
        url = self._get_title_node().attrib['href']
        if re.match(r".*/.*/download/[a-zA-Z0-9_]+", url):
            return "/".join(url.split("/")[:-2])
        return url

    @field_builder(GameInfo.details)
    def scrape_itch_game_page_info(self):
        try:
            page_tree = self.get_page_html_tree(self._get_url())
        except requests.HTTPError:
            return ItchGamePageInfo()
        return GamePageScraper(self.cookie, page_tree).build(ItchGamePageInfo)
