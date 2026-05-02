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

## Execute Orchestration
```
chmod +x src/orchestrator.sh
./src/orchestrator.sh
```

## Test dbt
```
dbt test --target {environment}
```

## DuckDB Local UI to quickly query the data
```
curl https://install.duckdb.org | sh
duckdb ui
```