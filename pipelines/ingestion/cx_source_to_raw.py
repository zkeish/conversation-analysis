import os
from datetime import datetime

import duckdb
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv('ENV', 'dev')

class CX_s2r:

    @staticmethod
    def connect_db():
        return duckdb.connect(f"../../{ENV}.duckdb")

    @staticmethod
    def read_source():
