import pathlib
import os
import yaml


def get_root_dir():
    return pathlib.Path(__file__).parent.parent


def get_path(*children):
    return get_root_dir() / pathlib.Path(*children)


def load_config():
    with open(get_path("config.yml")) as f:
        return yaml.safe_load(f)


def get_data_path(*children):
    return get_path("data", *children)


def get_stats_homepage_url(config):
    return config["VIRTUAL_WARDS_STATS_HOMEPAGE"]


def get_raw_filename(date):
    return date.strftime("%Y_%m") + "_Monthly_Virtual_Ward.xlsx"
