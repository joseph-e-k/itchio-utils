import dataclasses
import functools
import re

from lxml import html

from GameInfo import GameInfo
from decorators import aggregator

from scrapers.Scraper import Scraper


@dataclasses.dataclass(frozen=True)
class BundleEntryScraper(Scraper):
    root_node: html.HtmlElement

    @functools.lru_cache
    def _get_title_node(self):
        return self.root_node.xpath(".//h2[@class='game_title']/a")[0]

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

    def get_game_info(self):
        itch_game_page_info = self.scrape_itch_game_page_info(self._get_url())

        return GameInfo(
            title=self._get_title_node().text,
            url=self._get_url(),
            summary=self._get_summary(),
            file_count=self._get_file_count(),
            operating_systems=self._get_operating_systems(),
            **dataclasses.asdict(itch_game_page_info)
        )
