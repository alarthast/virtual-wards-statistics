import pathlib
import os
import yaml
import datetime


def get_root_dir():
    """
    Get the root directory of the project.

    Returns:
        pathlib.Path: The root directory of the project.
    """
    return pathlib.Path(__file__).parent.parent


def get_path(*children: str):
    """
    Get the path to a file or directory within the project.

    Returns:
        pathlib.Path: The path to the file or directory.
    """
    return get_root_dir() / pathlib.Path(*children)


def load_config():
    """
    Loads the configuration file.

    Returns:
        dict: The configuration file as a dictionary.
    """
    with open(get_path("config.yml")) as f:
        return yaml.safe_load(f)


def get_data_path(*children: str):
    """
    Get the path to a file or directory within the data directory.

    Returns:
        pathlib.Path: The path to the file or directory.
    """
    return get_path("data", *children)


def get_stats_homepage_url(config: dict):
    """
    Get the URL of the publicly available NHS statistics on Virtual Wards.

    Args:
        config (dict): The configuration file as a dictionary.

    Returns:
        str: The URL of the statistics homepage.
    """
    return config["VIRTUAL_WARDS_STATS_HOMEPAGE"]


def generate_raw_filename(date: datetime.datetime):
    """
    Generate a standardised filename for a raw excel file of a given date.

    Args:
        date (datetime.datetime): The date of the raw excel file.

    Returns:
        str: The filename of the raw excel file.
    """
    return date.strftime("%Y_%m") + "_Monthly_Virtual_Ward.xlsx"
