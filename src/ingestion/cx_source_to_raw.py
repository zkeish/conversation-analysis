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

    def __init__(self, dataset: str) -> None:
        """Initialize the S2R (Source to Raw) ingestion pipeline.
        
        Args:
            dataset: The name of the dataset to ingest (e.g., 'cx').
        """
        self.DATASET = dataset
        self.TRACKING_TABLE = f'raw.{dataset}_processed_files'
        self.SOURCE_FOLDER_PATH = os.path.join(WORKING_DIR, 'external_data')
        self.TARGET_FOLDER_PATH = os.path.join(WORKING_DIR, f'raw/{dataset}')
        self.DATABASE = os.path.join(WORKING_DIR, f'pipelines/duckdb/{dataset}_ingestion.duckdb')
        self.METADATA = os.path.join(WORKING_DIR, 'pipelines/duckdb/models/schema.yml')

    def connect_db(self) -> duckdb.DuckDBPyConnection:
        """Establish a connection to the DuckDB database.
        
        Returns:
            A DuckDBPyConnection object connected to the dataset-specific database.
        """
        return duckdb.connect(self.DATABASE)

    def get_source_files(self) -> list:
        """Retrieve the list of files in the source folder.
        
        Returns:
            A list of file names in the external_data directory.
        """
        return os.listdir(self.SOURCE_FOLDER_PATH)

    def create_tracking_table(self) -> None:
        """Create the tracking table to record processed files.
        
        Creates the raw schema if it doesn't exist and a tracking table to store
        information about ingested files and their timestamps.
        """
        with self.connect_db() as con:
            con.sql('create schema if not exists raw')
            con.sql(f"""CREATE TABLE IF NOT EXISTS {self.TRACKING_TABLE} (
                                file_name VARCHAR PRIMARY KEY,
                                ingest_dtt TIMESTAMP
                            );""")

    def files_to_ingest(self, source_files: list) -> list:
        """Identify files that need to be ingested.
        
        Compares source files with those already tracked in the database to determine
        which files have not yet been ingested.
        
        Args:
            source_files: List of file names from the source folder.
            
        Returns:
            A list of file names that have not been previously ingested.
        """
        df = pd.DataFrame({"file_name": source_files})
        with self.connect_db() as con:
            files = con.sql(f'select file_name from df where file_name not in (select file_name from {self.TRACKING_TABLE})').fetchnumpy()["file_name"].tolist()
        return files

    def ingest_files(self, files: list) -> None:
        """Ingest files from source to raw storage in parquet format.
        
        Converts each source file into parquet format and stores it in the target folder.
        Tracks successfully ingested files in the tracking table.
        
        Args:
            files: List of file names to ingest.
            
        Raises:
            Exception: If an error occurs during file transfer.
        """
        for file in files:
            try:
                source = os.path.join(self.SOURCE_FOLDER_PATH, file)
                target_file_name = Utils.format_file_datetime(self.DATASET, CURRENT_TIMESTAMP, 'parquet')
                target = os.path.join(self.TARGET_FOLDER_PATH, target_file_name)
                with self.connect_db() as con:
                    df = con.sql(f"select * from '{source}'").to_arrow_table()
                    Utils.mkdirs(self.TARGET_FOLDER_PATH)
                    pq.write_table(df, target)
                    con.sql(f"insert into {self.TRACKING_TABLE} (file_name, ingest_dtt) VALUES ('{file}', CURRENT_TIMESTAMP);")
            except Exception as e:
                print(f'Issue transfering file to raw storage:')
                raise e
            
    def main(self):
        """Run the complete source to raw ingestion pipeline.
        
        Orchestrates the entire process: creates tracking table, retrieves source files,
        identifies new files to ingest, and ingests them.
        """
        self.create_tracking_table()
        source_files = self.get_source_files()
        files = self.files_to_ingest(source_files)
        self.ingest_files(files)


# Process cx dataset
if __name__ == "__main__":
    S2R('cx').main()
