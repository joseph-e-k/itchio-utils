import dataclasses
from concurrent.futures.thread import ThreadPoolExecutor

from records.GameInfo import GameInfo
from scrapers.Scraper import Scraper
from scrapers.BundleEntryScraper import BundleEntryScraper


BUNDLE_PAGE_URL_FORMAT = "https://itch.io/bundle/download/{}?page={}"


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

    def bundle_entry_html_to_game_info(self, entry_node):
        return BundleEntryScraper(self.cookie, entry_node).build(GameInfo)

    def parse_bundle_page(self, html_tree):
        game_rows = html_tree.xpath("//div[@class='game_row']")

        with ThreadPoolExecutor() as executor:
            games = executor.map(self.bundle_entry_html_to_game_info, game_rows, timeout=60)

        return list(games)
