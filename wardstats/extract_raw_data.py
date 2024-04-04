import os
import bs4
import requests
import logging
from datetime import datetime
from wardstats.utils import (
    load_config,
    get_stats_homepage_url,
    get_data_path,
    get_raw_filename,
)
from wardstats.config import RAW


def get_page_content(url: str):
    return requests.get(url).content


def get_beautiful_soup(url: str):
    return bs4.BeautifulSoup(get_page_content(url), "html.parser")


class VirtualWardsStatsDownloader:
    def __init__(self, homepage: str):
        self.homepage = homepage
        return

    def get_soup(self):
        return get_beautiful_soup(self.homepage)

    def get_data_links(self):
        return filter(self.is_data_link, self.get_soup().find_all("a"))

    def download_data(self, overwrite=False):
        for link in self.get_data_links():
            self.download_file(link, overwrite)
        return

    def download_file(self, link: bs4.element.Tag, overwrite: bool):
        filename = self.convert_link_text_to_filename(link.text)
        filepath = get_data_path(RAW, filename)
        if overwrite or not os.path.exists(filepath):
            content = get_page_content(link["href"])
            with open(filepath, "wb") as f:
                f.write(content)
            logging.info(f"Downloaded {filepath}")
        return

    @staticmethod
    def is_data_link(link: bs4.element.Tag):
        return link["href"].endswith(".xlsx")

    def convert_link_text_to_filename(self, text: str):
        date = self.extract_date_from_text(text)
        name = get_raw_filename(date)
        return name

    def extract_date_from_text(self, text: str):
        bits = text.split(" ")
        # Find the year
        for j, bit in enumerate(bits):
            if bit.isdigit():
                year = bit
                break
        month = bits[j - 1]
        date = datetime.strptime(" ".join([month, year]), "%B %Y")
        return date


def main():
    config = load_config()
    homepage = get_stats_homepage_url(config)
    downloader = VirtualWardsStatsDownloader(homepage)
    downloader.download_data(overwrite=True)
    return


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    main()
