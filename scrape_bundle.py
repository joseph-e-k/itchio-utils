import argparse
import csv
import os
from enum import Enum

from command_line_utils import prompt_user_choice
from records.GameInfo import GameInfo
from scrapers import connect


BUNDLE_PAGE_URL_FORMAT = "https://itch.io/bundle/download/{}?page={}"
OUTPUT_ENCODING = "UTF-8"
DEFAULT_OUTPUT_PATH = "./bundle_scraping_output.csv"
PAGE_IN_BUNDLE_HEADER = "Page in bundle"


class OutputFileConflictActions(Enum):
    OVERWRITE = "O"
    CONTINUE = "C"
    PROMPT = "P"


def open_output_file(path, mode):
    return open(path, mode, newline="", encoding=OUTPUT_ENCODING)


def create_output_file(path):
    with open_output_file(path, "w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(GameInfo.get_user_facing_field_names() + (PAGE_IN_BUNDLE_HEADER,))


def prompt_for_output_path_conflict(path):
    choices = {
        "O": ("overwrite", OutputFileConflictActions.OVERWRITE),
        "C": ("continue", OutputFileConflictActions.CONTINUE),
        "P": ("enter a new path", OutputFileConflictActions.PROMPT)
    }

    chosen_action = prompt_user_choice(f"Path already exists: {path}", choices)
    if chosen_action == OutputFileConflictActions.PROMPT:
        path = input("Enter a different path: ")

    return path, chosen_action


def guarantee_output_path(path, conflict_action):
    while os.path.exists(path) and conflict_action == OutputFileConflictActions.PROMPT:
        path, conflict_action = prompt_for_output_path_conflict(path)

    if not os.path.exists(path) or conflict_action == OutputFileConflictActions.OVERWRITE:
        create_output_file(path)

    return path


def dump_game_info(games, path, page_in_bundle):
    with open(path, "a", newline="", encoding=OUTPUT_ENCODING) as output_file:
        writer = csv.writer(output_file)
        for game in games:
            writer.writerow(game.get_user_facing_field_values() + (page_in_bundle,))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("slug")
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "-o",
        "--overwrite",
        dest="output_file_conflict_action",
        action="store_const",
        const=OutputFileConflictActions.OVERWRITE
    )
    parser.add_argument(
        "-c",
        "--continue",
        dest="output_file_conflict_action",
        action="store_const",
        const=OutputFileConflictActions.CONTINUE
    )
    parser.set_defaults(output_file_conflict_action=OutputFileConflictActions.PROMPT)
    return parser.parse_args()


def main():
    args = parse_args()
    connection = connect(args.username, args.password).get_bundle(args.slug)

    print("Scraping bundle metadata (page count, etc.)")
    page_count = connection.get_bundle_page_count()

    output_path = guarantee_output_path(args.output_path, args.output_file_conflict_action)

    with open_output_file(output_path, "r") as old_output_file:
        dict_reader = csv.DictReader(old_output_file)
        starting_page_number = max((int(entry[PAGE_IN_BUNDLE_HEADER]) for entry in dict_reader), default=0) + 1

    print(f"{starting_page_number - 1} / {page_count} pages already scraped")

    for page_number in range(starting_page_number, page_count + 1):
        print(f"Handling page {page_number} / {page_count}...")
        print("... Scraping")
        games = connection.scrape_bundle_page(page_number)
        print(f"... Writing to {output_path}")
        dump_game_info(games, output_path, page_number)


if __name__ == '__main__':
    main()
