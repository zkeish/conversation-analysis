#!/bin/bash
set -e  # stop on any error

echo "Starting pipeline..."

echo "Ingesting Raw data..."
python3.12 src/ingestion/cx_source_to_raw.py

if [ $? -eq 0 ]; then
    echo "Source to raw succeeded, starting dbt models..."
    cd ./pipelines/duckdb
    dbt run
else
    echo "Ingestion failed, skipping dbt run"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo "dbt run succeeded, starting embeddings..."
    cd ../../src/db_scripts
    python embed_vectors.py
else
    echo "dbt run failed, skipping embeddings"
    exit 1
fi


if [ $? -eq 0 ]; then
    echo "embeddings succeeded, lets talk to an agent about the tickets..."
    cd ../../src/agent
    python app.py
else
    echo "embeddings failed, skipping agent"
    exit 1
fi

echo "Pipeline complete!"