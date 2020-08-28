import functools
import re
import argparse
from dataclasses import dataclass
from typing import Set, Optional

import requests
from lxml import html

from authentication import log_in_and_get_cookie

BUNDLE_PAGE_URL_FORMAT = "https://itch.io/bundle/download/{}?page={}"
DEFAULT_OUTPUT_PATH = "./bundle_scraping_output.txt"


@dataclass
class GameInfo:
    title: str
    summary: str
    url: str
    operating_systems: Set[str]
    file_count: int
    bundle_page_number: Optional[int]


def get_bundle_page_count(bundle_slug, cookie):
    first_page_html_tree = get_bundle_page_html_tree(bundle_slug, cookie, 1)
    page_count_node = first_page_html_tree.xpath("//span[@class='pager_label']/a")[0]
    return int(page_count_node.text)


def html_to_game_info(html_tree):
    title_node = html_tree.xpath(".//h2[@class='game_title']/a")[0]
    summary_node = html_tree.xpath(".//div[@class='meta_row game_short_text']")[0]
    try:
        file_count_node = html_tree.xpath(".//div[@class='meta_row file_count']")[0]
    except IndexError:
        file_count_node = None

    return GameInfo(
        title=title_node.text,
        url=title_node.attrib['href'],
        summary=summary_node.text,
        file_count=int(re.match(r"(\d+) files?", file_count_node.text).group(1)) if file_count_node is not None else 1,
        operating_systems=set(),
        bundle_page_number=None
    )


def scrape_bundle_page(bundle_slug, page_number, cookie):
    page_html_tree = get_bundle_page_html_tree(bundle_slug, cookie, page_number)

    games_in_page = parse_bundle_page(page_html_tree)
    for game_info in games_in_page:
        game_info.bundle_page_number = page_number

    return games_in_page


@functools.lru_cache
def get_bundle_page_html_tree(bundle_slug, cookie, page_number):
    response = requests.request(
        method="GET",
        url=BUNDLE_PAGE_URL_FORMAT.format(bundle_slug, page_number),
        headers={
            "Cookie": cookie
        }
    )
    return html.fromstring(response.text)


def parse_bundle_page(html_tree):
    game_rows = html_tree.xpath("//div[@class='game_row']")
    games = []

    for game_row in game_rows:
        games.append(html_to_game_info(game_row))

    return games


def dump_game_info(games, path):
    with open(path, "w") as output_file:
        for game_info in games:
            block = f"Title: {game_info.title}\nSummary: {game_info.summary}\nURL: {game_info.url}\nFile count: {game_info.file_count}\nPage in bundle: {game_info.bundle_page_number}\n\n"
            try:
                output_file.write(block)
            except UnicodeEncodeError:
                pass


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("slug")
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main():
    args = parse_args()
    cookie = log_in_and_get_cookie(args.username, args.password)
    games = []

    print("Scraping bundle metadata (page count, etc.)")
    page_count = get_bundle_page_count(args.slug, cookie)

    for page_number in range(1, page_count + 1):
        print(f"Scraping page {page_number} / {page_count}")
        games += scrape_bundle_page(args.slug, page_number, cookie)

    print(f"Writing scraped data to {args.output_path}")
    dump_game_info(games, args.output_path)


if __name__ == '__main__':
    main()
