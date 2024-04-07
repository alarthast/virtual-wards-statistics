import os
import pandas as pd
import logging
from wardstats.config import STAGING, PROCESSED
from wardstats.utils import get_data_path, load_config

logging.getLogger().setLevel(logging.INFO)


def main():
    config = load_config()
    processed_path = get_data_path(PROCESSED, config["DATA_FILENAME"])
    files = os.listdir(get_data_path(STAGING))
    files.sort()  # Ensure files are in date order
    dfs = [pd.read_csv(get_data_path(STAGING, file)) for file in files]
    combined_df = pd.concat(dfs)
    combined_df.to_csv(
        processed_path,
        index=False,
    )
    logging.info(f"Written combined file to {processed_path}.")
    return


if __name__ == "__main__":
    main()
