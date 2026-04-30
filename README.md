# conversation-analysis
Parses raw conversation data and intelligently provides context regarding anomalies

# Setup

## Create and Activate Python Virtual Environment
```
python3.12 -m venv .venv
source .venv/bin/activate
```

## pip install requirements
```
python3.12 -m pip install -r requirements.txt
```

## Run dbt 
```
dbt run --target {environment}
```

## Test dbt
```
dbt test --target {environment}
```

## DuckDB Local UI for Visualizing the data
```
curl https://install.duckdb.org | sh
duckdb ui
```