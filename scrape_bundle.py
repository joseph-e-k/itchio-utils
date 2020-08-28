import csv
import functools
import re
import argparse

import requests
from lxml import html

from GameInfo import GameInfo
from authentication import log_in_and_get_cookie

BUNDLE_PAGE_URL_FORMAT = "https://itch.io/bundle/download/{}?page={}"
ENCODING = "UTF-8"
DEFAULT_OUTPUT_PATH = "./bundle_scraping_output.csv"


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

    operating_systems = set()
    operating_system_nodes = html_tree.xpath(".//div[@class='meta_row']/span[contains(@title, 'Available for ')]")
    for node in operating_system_nodes:
        operating_systems.add(re.match(r"Available for (\w+)", node.attrib["title"]).group(1))

    return GameInfo(
        title=title_node.text,
        url=title_node.attrib['href'],
        summary=summary_node.text,
        file_count=int(re.match(r"(\d+) files?", file_count_node.text).group(1)) if file_count_node is not None else 1,
        operating_systems=operating_systems
    )


def scrape_bundle_page(bundle_slug, page_number, cookie):
    page_html_tree = get_bundle_page_html_tree(bundle_slug, cookie, page_number)
    return parse_bundle_page(page_html_tree)


@functools.lru_cache
def get_bundle_page_html_tree(bundle_slug, cookie, page_number):
    response = requests.request(
        method="GET",
        url=BUNDLE_PAGE_URL_FORMAT.format(bundle_slug, page_number),
        headers={
            "Cookie": cookie
        }
    )
    return html.fromstring(response.content.decode(ENCODING))


def parse_bundle_page(html_tree):
    game_rows = html_tree.xpath("//div[@class='game_row']")
    games = []

    for game_row in game_rows:
        games.append(html_to_game_info(game_row))

    return games


def dump_game_info(games, path, page_in_bundle):
    with open(path, "a", newline="", encoding=ENCODING) as output_file:
        writer = csv.writer(output_file)
        for game in games:
            writer.writerow(game.get_friendly_field_values() + (page_in_bundle,))


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

    print("Scraping bundle metadata (page count, etc.)")
    page_count = get_bundle_page_count(args.slug, cookie)

    # Refresh output file
    with open(args.output_path, "w", newline="", encoding=ENCODING) as output_file:
        writer = csv.writer(output_file)
        writer.writerow(GameInfo.get_friendly_field_names() + ("Page in bundle",))

    for page_number in range(1, page_count + 1):
        print(f"Handling page {page_number} / {page_count}...")
        print("... Scraping")
        games = scrape_bundle_page(args.slug, page_number, cookie)
        print(f"... Writing to {args.output_path}")
        dump_game_info(games, args.output_path, page_number)


if __name__ == '__main__':
    main()
