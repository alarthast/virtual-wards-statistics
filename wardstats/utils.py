import pathlib
import yaml
import datetime
import pandas as pd
import geopandas as gpd
from wardstats.config import STATIC, DATE


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


def get_geojson_dataframe(config):
    filename = config["GEOJSON_FILENAME"]
    filepath = get_data_path(STATIC, filename)
    return gpd.read_file(filepath).to_crs(epsg=4326)


def get_icb_code_lookup(config):
    filename = config["ICB_CODE_LOOKUP_FILENAME"]
    filepath = get_data_path(STATIC, filename)
    df = pd.read_excel(filepath)
    df.set_index("ICB22CD", inplace=True)
    lookup = pd.Series(df["ICB22CDH"]).to_dict()
    return lookup


def get_icb_boundaries(config):
    lookup = get_icb_code_lookup(config)
    gdf = get_geojson_dataframe(config)
    gdf = gdf.replace({"ICB22CD": lookup})
    boundaries = eval(gdf.to_json())
    return boundaries


def get_icb_name_lookup(boundaries: dict):
    df = gpd.GeoDataFrame.from_features(boundaries)[["ICB22CD", "ICB22NM"]].copy()
    df.set_index("ICB22CD", inplace=True)
    lookup = pd.Series(df["ICB22NM"]).to_dict()
    return lookup


def filter_date(df, date=None):
    if date is None:
        date = df[DATE].max()
    filtered = df[df[DATE] == date].copy()
    if len(filtered) == 0:
        raise ValueError(f"No data available for {date}, max is {df[DATE].max()}")
    return filtered
