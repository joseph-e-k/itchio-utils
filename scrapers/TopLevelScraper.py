import dataclasses

from scrapers.Scraper import Scraper
from scrapers.BundleScraper import BundleScraper


@dataclasses.dataclass(frozen=True)
class TopLevelScraper(Scraper):
    def get_bundle(self, bundle_slug):
        return BundleScraper(slug=bundle_slug, **dataclasses.asdict(self))
