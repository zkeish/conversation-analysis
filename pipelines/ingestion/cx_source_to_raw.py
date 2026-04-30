import os
from datetime import datetime

from utils import Utils

import duckdb
from dotenv import load_dotenv
import pandas as pd
import yaml


load_dotenv()

ENV = os.getenv('ENV', 'dev')
WORKING_DIR = os.getenv('WORKING_DIR', os.getcwd())
CURRENT_TIMESTAMP = datetime.now()

class S2R:

    def __init__(self, dataset):
        self.TRACKING_TABLE = f'bronze.{dataset}_processed_files'
        self.BRONZE_TABLE = f'bronze.b_{dataset}_convo'
        self.SOURCE_FOLDER_PATH = os.path.join(WORKING_DIR, 'external_data')
        self.TARGET_FOLDER_PATH = os.path.join(WORKING_DIR, f'raw/{dataset}')
        self.DATABASE = os.path.join(WORKING_DIR, f'pipelines/duckdb/{ENV}.duckdb')
        self.METADATA = os.path.join(WORKING_DIR, 'pipelines/duckdb/models/schema.yml')

    def connect_db(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.DATABASE)

    def get_source_files(self) -> list:
        return os.listdir(self.SOURCE_FOLDER_PATH)

    def create_tracking_table(self) -> None:
        with self.connect_db() as con:
            con.sql('create schema if not exists bronze')
            con.sql(f"""CREATE TABLE IF NOT EXISTS {self.TRACKING_TABLE} (
                                file_name VARCHAR PRIMARY KEY,
                                ingest_dtt TIMESTAMP
                            );""")

    def files_to_ingest(self, source_files: list) -> list:
        df = pd.DataFrame({"file_name": source_files})
        with self.connect_db() as con:
            files = con.sql(f'select file_name from df where file_name not in (select file_name from {self.TRACKING_TABLE})').fetchnumpy()["file_name"].tolist()
        return files
    
    def read_silver_metadata(self) -> list:

        with open(self.METADATA, 'r') as f:
            schema = yaml.safe_load(f) or {}

        metadata = []
        for table in schema.get('models', []):
            table_name = table.get('name')
            if not table_name:
                continue
            columns = table.get('columns', [])
            for col in columns:
                col_name = col.get('name')
                col_data_type = col.get('data_type')
                metadata.append([col_name, col_data_type])
        return metadata

    def analyze_schema(self, source_path: str) -> tuple[list, list, list]:
        select_col = []
        alter_table = []
        create_table = []

        with self.connect_db() as con:
            try:
                con.sql(f"SELECT * FROM {self.BRONZE_TABLE} LIMIT 1")
                exists = True
            except:
                exists = False

            source = con.sql(f"""
                DESCRIBE SELECT *
                FROM '{source_path}'
                """).fetchall()
            
            if exists:
                target = con.sql(f"""
                    DESCRIBE SELECT *
                    FROM {self.BRONZE_TABLE}
                    """).fetchall()
                target = [c[0] for c in source]
            else:
                target = []
            
            source = [c[0] for c in source]
            metadata = self.read_silver_metadata()

            for col in metadata:
                col_name = col[0]
                col_data_type = col[1]

                if col_name not in source:
                    select_col.append(f'NULL AS {col}')
                    if not exists:
                        create_table.append(f'{col_name} {col_data_type}')
                elif col_name not in target:
                    select_col.append(col_name)
                    if exists:
                        alter_table.append(f'ALTER TABLE {self.BRONZE_TABLE} ADD COLUMN {col_name} {col_data_type};')
                    else:
                        create_table.append(f'{col_name} {col_data_type}')
                else:
                    select_col.append(col_name)

        return select_col, alter_table, create_table
    
    def load_data(self, select_col: list, alter_table: list, create_table: list, source_path: str, file_name: str) -> None:
        select_str = ", ".join(select_col)
        create_table_str = ", ".join(create_table)
        
        with self.connect_db() as con:
            if len(alter_table) > 0:
                for alt_sql in alter_table:
                    con.sql(alt_sql)

            if len(create_table) > 0:
                con.sql(f"""CREATE TABLE IF NOT EXISTS {self.BRONZE_TABLE} (
                                    {create_table_str}
                                    , file_name varchar
                                );""")
            
            con.sql(f"insert into {self.BRONZE_TABLE} select {select_str}, '{source_path}' as file_path from '{source_path}';")
            con.sql(f"insert into {self.TRACKING_TABLE} (file_name, ingest_dtt) VALUES ('{file_name}', CURRENT_TIMESTAMP);")

    def ingest_files(self, files: list):
        for file in files:
            try:
                source = os.path.join(self.SOURCE_FOLDER_PATH, file)
                target_file_name = Utils.format_file_datetime('cx_data', CURRENT_TIMESTAMP, 'json')
                target = os.path.join(self.TARGET_FOLDER_PATH, target_file_name)
                Utils.cp(source, target)
                select_col, alter_table, create_table = self.analyze_schema(target)
                self.load_data(select_col, alter_table, create_table, target, file)
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
