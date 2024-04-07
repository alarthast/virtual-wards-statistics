import os
import pandas as pd
import numpy as np
import multiprocessing as mp
import logging
from datetime import datetime
from wardstats.utils import get_data_path, load_config
from wardstats.config import (
    RAW,
    STAGING,
    OCCUPANCY,
    ICB_CODE,
    SUPPRESSED,
    DATE,
    REGION,
    NAME,
)

logging.getLogger().setLevel(logging.INFO)


class ExcelFileProcessor:
    def __init__(self, raw_filename: str):
        """A class to process the raw excel files into a clean csv format.
        Args:
            raw_filename (str): The name of the raw excel file.
        """
        self.raw_filename = raw_filename
        self.date = self.get_date()
        self.staging_filename = self.date.strftime("%Y_%m") + ".csv"
        return

    def get_date(self):
        """
        Extracts the date from the raw filename.

        Returns:
            datetime: The date extracted from the raw filename.
        """
        bits = self.raw_filename.split("_")
        year = int(bits[0])
        month = int(bits[1])
        return datetime.strptime(f"{year}-{month}", "%Y-%m")

    def read_in_raw_file(self):
        """
        Reads in the raw excel file as a dataframe.

        Returns:
            pd.DataFrame: The raw dataframe.
        """
        file = pd.ExcelFile(get_data_path(RAW, self.raw_filename))
        df = pd.read_excel(file, file.sheet_names[1])
        return df

    def transform_dataframe(self, df: pd.DataFrame):
        """
        Applies all cleaning and transformation steps to the raw dataframe.

        Args:
            df (pd.DataFrame): The raw dataframe.

        Returns:
            pd.DataFrame: The transformed dataframe.
        """
        df = self.extract_raw_dataframe(df)
        df = self.rename_columns(df)
        df = df.drop(columns=[REGION, NAME])
        df = self.drop_rows_with_invalid_icb_code(df)
        df = self.handle_occupancy_suppressions(df)
        df = self.add_date_column(df)
        return df

    def write_clean_file_to_staging(self):
        """
        Writes the cleaned dataframe to the staging directory as a csv file.
        """
        df = self.read_in_raw_file()
        df = self.transform_dataframe(df)
        df.to_csv(get_data_path(STAGING, self.staging_filename), index=False)
        logging.info(f"Processed {self.raw_filename}.")
        return

    def extract_raw_dataframe(self, df: pd.DataFrame):
        """
        Extracts only the raw data table from the parsed excel sheet.

        Args:
            df (pd.DataFrame): The dataframe loaded by pd.read_excel.

        Returns:
            pd.DataFrame: The raw data table.
        """
        df = self.remove_leading_rows(df)
        df = self.promote_header_row(df)
        df = self.remove_nan_columns(df)
        return df

    def remove_leading_rows(self, df: pd.DataFrame):
        """Removes the metadata rows at the top of the excel sheet.

        Args:
            df (pd.DataFrame): The dataframe loaded by pd.read_excel.

        Returns:
            pd.DataFrame: The dataframe with the metadata rows removed.
        """
        header_row = self._index_header_row(df)
        return df[header_row:].copy()

    def _index_header_row(self, df: pd.DataFrame):
        """

        Finds the row index of the header row in the raw data table.

        Args:
            df (pd.DataFrame): The dataframe loaded by pd.read_excel.
        Returns:
            int: The index of the header row.
        """
        # Assume the last column is numeric which is the case for all the files
        col = df.columns[-1]
        first_numeric_row = np.where(df[col].astype(str).str[0].str.isnumeric())[0][0]
        header_row = first_numeric_row - 1
        return header_row

    def promote_header_row(self, df: pd.DataFrame):
        """
        Promotes the header row to the column names.

        Args:
            df (pd.DataFrame): Dataframe with column names in the first row.

        Returns:
            pd.DataFrame: Dataframe with column names as the column headers.
        """
        columns = df.iloc[0].tolist()
        df = df[1:].reset_index(drop=True)
        df.columns = columns
        return df

    def remove_nan_columns(self, df: pd.DataFrame):
        """
        Removes columns that are entirely NaN.

        Args:
            df (pd.DataFrame)

        Returns:
            pd.DataFrame: The dataframe without columns that are entirely NaN.
        """
        return df.loc[:, ~df.isna().all()].copy()

    def rename_columns(self, df: pd.DataFrame):
        """
        Renames the columns to shorter, more readable names.

        Args:
            df (pd.DataFrame): The dataframe with the original column names.

        Returns:
            pd.DataFrame: The dataframe with the renamed column names.
        """
        df.columns = [i.split("\n")[0].strip() for i in df.columns]  # Remove footnotes
        config = load_config()
        return df.rename(columns=config["COLUMN_NAMES"])

    def drop_rows_with_invalid_icb_code(self, df: pd.DataFrame):
        """
        Drops rows with invalid ICB codes (less than 3 characters).
        In effect this removes the "England" row.

        Args:
            df (pd.DataFrame): The dataframe with the ICB code column.

        Returns:
            pd.DataFrame: The dataframe with invalid ICB codes removed.
        """
        return df[df[ICB_CODE].str.len() > 2].copy()

    def handle_occupancy_suppressions(self, df: pd.DataFrame):
        """
        Creates a new column to indicate if the occupancy value was suppressed,
        then fills in the suppressed values with 100%.

        Args:
            df (pd.DataFrame): The dataframe with the occupancy column.

        Returns:
            pd.DataFrame: The dataframe with suppressed values filled in.
        """
        df[SUPPRESSED] = df[OCCUPANCY].astype(str).str[-1] == "*"
        sp = df[df[SUPPRESSED]].copy()
        nsp = df[~df[SUPPRESSED]].copy()
        sp[OCCUPANCY] = 1.0
        df = pd.concat([sp, nsp]).reset_index(drop=True)
        return df

    def add_date_column(self, df: pd.DataFrame):
        """
        Adds a column with the date corresponding to the file.

        Args:
            df (pd.DataFrame)

        Returns:
            pd.DataFrame: The dataframe with the date column added.
        """
        df.insert(0, DATE, self.date)
        return df


def process_file(raw_filename: str):
    """
    Wrapped function to process a single file.

    Args:
        raw_filename (str): The name of the raw excel file.
    """
    if raw_filename.endswith(".xlsx") and not raw_filename.startswith("~"):
        proc = ExcelFileProcessor(raw_filename)
        proc.write_clean_file_to_staging()
    else:
        logging.info(f"Skipping {raw_filename}.")
    return


def main():
    files = os.listdir(get_data_path(RAW))
    print(files)
    with mp.Pool(min(mp.cpu_count(), len(files))) as pool:
        pool.map(process_file, files)
        pool.close()
        pool.join()

    return


if __name__ == "__main__":
    main()
