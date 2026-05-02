# conversation-analysis
Parses raw conversation data and intelligently provides context regarding anomalies.

## Overview
This project ingests customer conversation data, processes it through a dbt pipeline in DuckDB, and generates insights like resolved issues and anomaly detection.

## Part 1
- [Anomaly detection notebook](src/eda/anomalies.ipynb)

## Part 2
- [Chatbot](src/agent/app.py)
- [Results](chatbot_interactions.md)

## Prerequisites
- Python 3.12
- DuckDB (for local querying)

## Installation
1. Create and activate a Python virtual environment:
   ```
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```
   python3.12 -m pip install -r requirements.txt
   ```

## Usage
1. Run the orchestration script:
   ```
   chmod +x src/orchestrator.sh
   ./src/orchestrator.sh
   ```

2. Query data locally with DuckDB UI:
   ```
   curl https://install.duckdb.org | sh
   duckdb ui
   ```

3. Talk to chatbot in command line:
   ```
   Open Ticket > {Your ticket context goes here}
   ```
   Note: Type `quit` to exit the chat

## Data Pipeline
The dbt pipeline transforms raw data into structured layers for analysis. Below is a simplified dataflow diagram:

```mermaid
graph TD
A[Raw Data JSON files] --> B[Bronze Layer <br/> Ingest raw data]
B --> C[Silver Layer <br/> Clean and deduplicate]
C --> D[Gold Layer <br/> Issue dimensions]
C --> E[Gold Layer <br/> Metadata dimensions]
C --> F[Gold Layer <br/> Message facts]
D --> G[CX Layer <br/> Resolved conversations with embeddings]
E --> G
F --> G
D --> H[CX Layer <br/> Anomaly detection view]
E --> H
```

## Database Schema
The data is organized in a star schema with dimension and fact tables:

```mermaid
erDiagram

    FACT_CX_MESSAGE ||--o{ DIM_CX_ISSUE : "has"
    FACT_CX_MESSAGE }o--|| DIM_CX_METADATA : "has"
    
    DIM_CX_ISSUE {
        ubigint issue_key "surrogate key, PK"
        ubigint conversation_key "FK"
        varchar primary_issue
        varchar issue_type
        varchar secondary_issue
        boolean issue_resolved
        varchar resolution_type
        varchar resolution_notes
    }
    
    DIM_CX_METADATA {
        ubigint conversation_key "surrogate key, PK, FK"
        ubigint customer_key "FK"
        varchar conversation_id
        varchar customer_id
        varchar category
        varchar issue_type
        varchar product
        varchar status
        varchar priority
        timestamp conversation_first_message_dtt
        timestamp conversation_last_message_dtt
    }
    
    FACT_CX_MESSAGE {
        ubigint message_key "surrogate key, PK"
        ubigint conversation_key "FK"
        ubigint customer_key "FK"
        varchar message_id
        varchar sender_role
        varchar message_text
        timestamp message_sent_dtt
    }
    
    
```

