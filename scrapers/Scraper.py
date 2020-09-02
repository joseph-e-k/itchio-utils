import dataclasses
import functools

import requests
from lxml import html


ITCH_WEB_ENCODING = "UTF-8"


@dataclasses.dataclass(frozen=True)
class Scraper:
    cookie: str

    @functools.lru_cache
    def get_page_html_tree(self, url):
        response = requests.get(
            url=url,
            headers={
                "Cookie": self.cookie
            }
        )

        response.raise_for_status()

        return html.fromstring(response.content.decode(ITCH_WEB_ENCODING))
