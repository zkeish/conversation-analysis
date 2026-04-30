import os
from datetime import datetime

from utils import Utils

import duckdb
from dotenv import load_dotenv
import pandas as pd
import pyarrow.parquet as pq


load_dotenv()

ENV = os.getenv('ENV', 'dev')
WORKING_DIR = os.getenv('WORKING_DIR', os.getcwd())
CURRENT_TIMESTAMP = datetime.now()

class S2R:

    def __init__(self, dataset):
        self.DATASET = dataset
        self.TRACKING_TABLE = f'raw.{dataset}_processed_files'
        self.SOURCE_FOLDER_PATH = os.path.join(WORKING_DIR, 'external_data')
        self.TARGET_FOLDER_PATH = os.path.join(WORKING_DIR, f'raw/{dataset}')
        self.DATABASE = os.path.join(WORKING_DIR, f'pipelines/duckdb/{dataset}_ingestion.duckdb')
        self.METADATA = os.path.join(WORKING_DIR, 'pipelines/duckdb/models/schema.yml')

    def connect_db(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.DATABASE)

    def get_source_files(self) -> list:
        return os.listdir(self.SOURCE_FOLDER_PATH)

    def create_tracking_table(self) -> None:
        with self.connect_db() as con:
            con.sql('create schema if not exists raw')
            con.sql(f"""CREATE TABLE IF NOT EXISTS {self.TRACKING_TABLE} (
                                file_name VARCHAR PRIMARY KEY,
                                ingest_dtt TIMESTAMP
                            );""")

    def files_to_ingest(self, source_files: list) -> list:
        df = pd.DataFrame({"file_name": source_files})
        with self.connect_db() as con:
            files = con.sql(f'select file_name from df where file_name not in (select file_name from {self.TRACKING_TABLE})').fetchnumpy()["file_name"].tolist()
        return files

    def ingest_files(self, files: list):
        for file in files:
            try:
                source = os.path.join(self.SOURCE_FOLDER_PATH, file)
                target_file_name = Utils.format_file_datetime(self.DATASET, CURRENT_TIMESTAMP, 'parquet')
                target = os.path.join(self.TARGET_FOLDER_PATH, target_file_name)
                with self.connect_db() as con:
                    df = con.sql(f"select * from '{source}'").to_arrow_table()
                    pq.write_table(df, target)
                    con.sql(f"insert into {self.TRACKING_TABLE} (file_name, ingest_dtt) VALUES ('{file}', CURRENT_TIMESTAMP);")
            except Exception as e:
                print(f'Issue transfering file to raw storage:')
                raise e
            
    def main(self):
        self.create_tracking_table()
        source_files = self.get_source_files()
        files = self.files_to_ingest(source_files)
        self.ingest_files(files)


# Process cx dataset
S2R('cx').main()
