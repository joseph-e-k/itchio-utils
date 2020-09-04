# itchio-utils

Utility scripts for working with itch.io. Not supported or endorsed by itch.io themselves in any way.

Developed and tested with Python 3.8.5.

## scrape_bundle.py

Scrapes the table of contents of a bundle and outputs a CSV (comma-separated values) file. Initially written shortly after the massive Racial Justice Bundle dropped and before itch.io had implemented search within bundles.

Usage: `python scrape_bundle.py USERNAME PASSWORD BUNDLE_NAME` or `python scrape_bundle.py USERNAME PASSWORD BUNDLE_NAME --output-path OUTPUT_PATH`

Where `USERNAME` and `PASSWORD` are the username and password you use to log in to itch.io, and `BUNDLE_NAME` is the name of the bundle to download, or a unique portion of the name. All these arguments are case-sensitive.

You may optionally also specify an output path; by default, output goes to `./bundle_scraping_output.csv`.

If a file already exists at the output path, you will be prompted to overwrite it, continue where a previous scrape was interrupted, or pick a new path. You can make the prompt unnecessary by adding `--overwrite` or `--continue` to the command line.
