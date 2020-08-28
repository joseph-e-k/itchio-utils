import argparse
import csv

from GameInfo import GameInfo
from connections import connect

BUNDLE_PAGE_URL_FORMAT = "https://itch.io/bundle/download/{}?page={}"
OUTPUT_ENCODING = "UTF-8"
DEFAULT_OUTPUT_PATH = "./bundle_scraping_output.csv"


def dump_game_info(games, path, page_in_bundle):
    with open(path, "a", newline="", encoding=OUTPUT_ENCODING) as output_file:
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
    connection = connect(args.username, args.password).get_bundle(args.slug)

    print("Scraping bundle metadata (page count, etc.)")
    page_count = connection.get_bundle_page_count()

    # Refresh output file
    with open(args.output_path, "w", newline="", encoding=OUTPUT_ENCODING) as output_file:
        writer = csv.writer(output_file)
        writer.writerow(GameInfo.get_friendly_field_names() + ("Page in bundle",))

    for page_number in range(1, page_count + 1):
        print(f"Handling page {page_number} / {page_count}...")
        print("... Scraping")
        games = connection.scrape_bundle_page(page_number)
        print(f"... Writing to {args.output_path}")
        dump_game_info(games, args.output_path, page_number)


if __name__ == '__main__':
    main()
