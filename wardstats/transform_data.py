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
    CAPACITY,
    CAPACITY_PER_POPULATION,
    POPULATION,
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
        self.raw_filename = raw_filename
        self.date = self.get_date()
        self.staging_filename = self.date.strftime("%Y_%m") + ".csv"
        return

    def get_date(self):
        bits = self.raw_filename.split("_")
        year = int(bits[0])
        month = int(bits[1])
        return datetime.strptime(f"{year}-{month}", "%Y-%m")

    def read_in_raw_file(self):
        file = pd.ExcelFile(get_data_path(RAW, self.raw_filename))
        df = pd.read_excel(file, file.sheet_names[1])
        return df

    def clean_dataframe(self, df: pd.DataFrame):
        df = self.extract_raw_dataframe(df)
        df = self.rename_columns(df)
        df = self.drop_unneeded_columns(df)
        df = self.drop_rows_with_invalid_icb_code(df)
        df = self.handle_occupancy_suppressions(df)
        df = self.add_date_column(df)
        return df

    def write_clean_file_to_staging(self):
        df = self.read_in_raw_file()
        df = self.clean_dataframe(df)
        df.to_csv(get_data_path(STAGING, self.staging_filename), index=False)
        logging.info(f"Processed {self.raw_filename}.")
        return

    def extract_raw_dataframe(self, df: pd.DataFrame):
        """
        Extracts only the raw data table from the parsed excel sheet.
        """
        df = self.remove_leading_rows(df)
        df = self.promote_header_row(df)
        df = self.remove_nan_columns(df)
        return df

    def remove_leading_rows(self, df: pd.DataFrame):
        header_row = self._index_header_row(df)
        return df[header_row:].copy()

    def _index_header_row(self, df: pd.DataFrame):
        col = df.columns[
            -1
        ]  # Assume the last column is numeric which is the case for all the files
        first_numeric_row = np.where(df[col].astype(str).str[0].str.isnumeric())[0][0]
        header_row = first_numeric_row - 1
        return header_row

    def promote_header_row(self, df: pd.DataFrame):
        columns = df.iloc[0].tolist()
        df = df[1:].reset_index(drop=True)
        df.columns = columns
        return df

    def remove_nan_columns(self, df: pd.DataFrame):
        return df.loc[:, ~df.isna().all()].copy()

    def rename_columns(self, df: pd.DataFrame):
        # Use shorter names for the analysis process
        df.columns = [i.split("\n")[0].strip() for i in df.columns]  # Remove footnotes
        config = load_config()
        return df.rename(columns=config["COLUMN_NAMES"])

    def drop_unneeded_columns(self, df: pd.DataFrame):
        df.drop(columns=[REGION, NAME], inplace=True)
        return df

    def drop_rows_with_invalid_icb_code(self, df: pd.DataFrame):
        return df[df[ICB_CODE].str.len() > 2].copy()

    def handle_occupancy_suppressions(self, df: pd.DataFrame):
        """
        Creates a new column to indicate if the occupancy value was suppressed,
        then fills in the suppressed values with 100%.
        """
        df[SUPPRESSED] = df[OCCUPANCY].astype(str).str[-1] == "*"
        sp, nsp = self.split_suppressed_or_not(df)
        sp[OCCUPANCY] = 1.0
        df = pd.concat([sp, nsp]).reset_index(drop=True)
        return df

    @staticmethod
    def split_suppressed_or_not(df: pd.DataFrame):
        sp = df[df[SUPPRESSED]].copy()
        nsp = df[~df[SUPPRESSED]].copy()
        return sp, nsp

    def add_date_column(self, df: pd.DataFrame):
        df.insert(0, DATE, self.date)
        return df


def process_file(raw_filename: str):
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
