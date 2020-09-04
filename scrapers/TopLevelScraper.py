import dataclasses
import re

from scrapers.Scraper import Scraper
from scrapers.BundleScraper import BundleScraper
from xpath_utils import xpath_repr

MY_BUNDLES_PAGE_URL = "https://itch.io/my-purchases/bundles"
BUNDLE_HREF_RE = re.compile(r"/bundle/download/([a-zA-Z0-9]+)$")


class AmbiguityException(Exception):
    pass


class NoMatchesException(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class TopLevelScraper(Scraper):
    def get_bundle(self, bundle_name):
        my_bundles_page = self.get_page_html_tree(MY_BUNDLES_PAGE_URL)
        matching_bundle_nodes = my_bundles_page.xpath(
            "//div[@class='primary_column']"
            "/section[@class='bundle_keys']"
            "/ul"
            "/li"
            f"/a[contains(text(), {xpath_repr(bundle_name)})]"
        )

        if len(matching_bundle_nodes) == 0:
            raise NoMatchesException()

        if len(matching_bundle_nodes) > 1:
            raise AmbiguityException([node.text for node in matching_bundle_nodes])

        href_re_match = BUNDLE_HREF_RE.match(matching_bundle_nodes[0].attrib["href"])

        return BundleScraper(slug=href_re_match.group(1), **dataclasses.asdict(self))
