# itchio-utils

Utility scripts for working with itch.io. Not supported or endorsed by itch.io themselves in any way.

Developed and tested with Python 3.8.5.

## scrape_bundle.py

Scrapes the table of contents of a bundle and outputs a CSV (comma-separated values) file. Initially written shortly after the massive Racial Justice Bundle dropped and before itch.io had implemented search within bundles.

Usage: `python scrape_bundle.py USERNAME PASSWORD SLUG` or `python scrape_bundle.py USERNAME PASSWORD SLUG --output-path OUTPUT_PATH`

Where `USERNAME` and `PASSWORD` are the username and password you use to log in to itch.io, and `SLUG` is the identifier for your copy of the bundle in question.

To find the correct `SLUG`, browse to the bundle in your library and you should find yourself at a URL that looks like `https://itch.io/bundle/download/XXXX`, where `XXXX` is a long string of letters and numbers. That `XXXX` is the slug; just copy and paste it.

You may optionally also specify an output path; by default, output goes to `./bundle_scraping_output.csv`.
