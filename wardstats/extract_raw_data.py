import os
import bs4
import requests
import logging
from datetime import datetime
from wardstats.utils import (
    load_config,
    get_stats_homepage_url,
    get_data_path,
    generate_raw_filename,
)
from wardstats.config import RAW


def get_page_content(url: str):
    """
    Get the content of a webpage.

    Args:
        url (str): The URL of the webpage.

    Returns:
        bytes: The content of the webpage.
    """
    return requests.get(url).content


def get_beautiful_soup(url: str):
    """
    Get the content of a webpage as a BeautifulSoup object.

    Args:
        url (str): The URL of the webpage.

    Returns:
        bs4.BeautifulSoup: The content of the webpage as a BeautifulSoup object.
    """
    return bs4.BeautifulSoup(get_page_content(url), "html.parser")


class VirtualWardsStatsDownloader:
    def __init__(self, homepage: str):
        """
        A class to download the raw data files from the NHS Virtual Wards statistics homepage.

        Args:
            homepage (str): The URL of the homepage.
        """
        self.homepage = homepage
        return

    def get_data_links(self):
        """
        Gets all the data links from the homepage.

        Returns:
            iterable: All the data links.
        """
        soup = get_beautiful_soup(self.homepage)
        return filter(self.is_data_link, soup.find_all("a"))

    def download_data(self, overwrite=False):
        """
        Downloads all the data files from the homepage.

        Args:
            overwrite (bool, optional): Whether to overwrite existing files. Defaults to False.
        """
        for link in self.get_data_links():
            self.download_file(link, overwrite)
        return

    def download_file(self, link: bs4.element.Tag, overwrite: bool):
        """
        Downloads a single file.

        Args:
            link (bs4.element.Tag): The link to the file obtained from a BeautifulSoup object.
            overwrite (bool): Whether to overwrite an existing downloaded file
        """
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
        """
        Determines whether a link is a data link (i.e. is an Excel file).

        Args:
            link (bs4.element.Tag): A link obtained from a BeautifulSoup object.

        Returns:
            bool: Whether the link is a data link.
        """
        return link["href"].endswith(".xlsx")

    def convert_link_text_to_filename(self, text: str):
        """
        Converts the text of a link to a filename.

        Args:
            text (str): The text of the link.

        Returns:
            str: The filename.
        """
        date = self.extract_date_from_text(text)
        name = generate_raw_filename(date)
        return name

    def extract_date_from_text(self, text: str):
        """
        Extracts the date from a link text.

        Args:
            text (str): The link text.

        Returns:
            datetime.datetime: The date extracted from the link text.
        """
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
