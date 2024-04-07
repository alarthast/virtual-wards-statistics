import pathlib
import yaml
import datetime
import pandas as pd
import geopandas as gpd
from wardstats.config import STATIC, DATE, ICB_CODE, ICB_NAME


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
    return config["VIRTUAL_WARDS_STATS_HOMEPAGE_URL"]


def generate_raw_filename(date: datetime.datetime):
    """
    Generate a standardised filename for a raw excel file of a given date.

    Args:
        date (datetime.datetime): The date of the raw excel file.

    Returns:
        str: The filename of the raw excel file.
    """
    return date.strftime("%Y_%m") + "_Monthly_Virtual_Ward.xlsx"


def get_geojson_dataframe(config: dict):
    """
    Get the boundaries of the ICBs as a GeoDataFrame.

    Args:
        config (dict): The configuration file as a dictionary.

    Returns:
        gpd.GeoDataFrame: The boundaries of the ICBs as a GeoDataFrame.
    """
    filename = config["GEOJSON_FILENAME"]
    filepath = get_data_path(STATIC, filename)
    return gpd.read_file(filepath).to_crs(epsg=4326)


def get_icb_code_lookup(config: dict):
    """
    Gets the lookup dictionary for long ICB code (Exxxxxx) to the three-letter ICB code.

    Args:
        config (dict): The configuration file as a dictionary.

    Returns:
        dict: The lookup dictionary.
    """
    filename = config["ICB_CODE_LOOKUP_FILENAME"]
    filepath = get_data_path(STATIC, filename)
    df = pd.read_excel(filepath)
    df.set_index("ICB22CD", inplace=True)
    lookup = pd.Series(df["ICB22CDH"]).to_dict()
    return lookup


def get_icb_boundaries(config: dict):
    """
    Get the boundaries of the ICBs as a GeoJSON dictionary.

    Args:
        config (dict): The configuration file as a dictionary.

    Returns:
        dict: The boundaries of the ICBs as a GeoJSON dictionary.
    """
    lookup = get_icb_code_lookup(config)
    gdf = get_geojson_dataframe(config)
    gdf = gdf.replace({"ICB22CD": lookup})
    boundaries = eval(gdf.to_json())
    return boundaries


def get_icb_name_lookup(boundaries: dict):
    """
    Get the lookup dictionary for ICB code to ICB name.

    Args:
        boundaries (dict): The boundaries of the ICBs as a GeoJSON dictionary.

    Returns:
        dict: The lookup dictionary.
    """
    df = gpd.GeoDataFrame.from_features(boundaries)[["ICB22CD", "ICB22NM"]].copy()
    df.set_index("ICB22CD", inplace=True)
    lookup = pd.Series(df["ICB22NM"]).to_dict()
    return lookup


def filter_date(df: pd.DataFrame, date=None):
    """
    Filter a dataframe to only include data from a specific date.

    Args:
        df (pd.DataFrame): The dataframe to filter.
        date (str or datetime, optional): The date to filter by. Defaults to None.

    Raises:
        ValueError: If no data is available for the specified date.

    Returns:
        pd.DataFrame: The filtered dataframe.
    """
    if date is None:
        date = df[DATE].max()
    filtered = df[df[DATE] == date].copy()
    if len(filtered) == 0:
        raise ValueError(f"No data available for {date}, max is {df[DATE].max()}")
    return filtered
