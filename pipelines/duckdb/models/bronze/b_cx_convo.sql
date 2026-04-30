select
      *
    , current_timestamp as load_dtt 
from read_parquet('../../raw/cx/*.parquet', filename=true)