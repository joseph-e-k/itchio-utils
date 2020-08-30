import re

import requests
from lxml import html

from scrapers.TopLevelScraper import TopLevelScraper


LOGIN_URL = "https://itch.io/login"


def connect(username, password):
    page_response = requests.get(LOGIN_URL)
    page_html_tree = html.fromstring(page_response.content)
    csrf_token_node = page_html_tree.xpath(".//input[@name='csrf_token']")[0]
    csrf_token = csrf_token_node.attrib["value"]
    itchio_token = re.search(r"\bitchio_token=([a-zA-Z0-9%]+);", page_response.headers["Set-Cookie"]).group(1)

    login_response = requests.post(
        LOGIN_URL,
        data=dict(
            username=username,
            password=password,
            csrf_token=csrf_token,
        ),
        headers={
            "Cookie": f"itchio_token={itchio_token}",
        }
    )

    login_response_cookies = login_response.headers["Set-Cookie"]
    login_token = re.search(r"\bitchio=([a-zA-Z0-9%]+);", login_response_cookies).group(1)
    cookie = f"itchio_token={itchio_token}; itchio={login_token}"

    return TopLevelScraper(cookie)
