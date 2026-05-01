import os
import duckdb
import pandas as pd
import requests
from dotenv import load_dotenv

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import google.genai as genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

with duckdb.connect('../pipelines/duckdb/dev.duckdb') as con:
    df = con.sql("""
        with cte_obt as (
        select 
              fm.*
            , issue_resolved
            , issue_type
            , product as product_name
            , resolution_type
            , resolution_notes
        from gold.fact_cx_message fm
        left join gold.dim_cx_metadata dm
        on fm.conversation_key = dm.conversation_key
        left join gold.dim_cx_issue i
        on fm.conversation_key = i.conversation_key
        )
        select
          conversation_key
        , issue_type
        , product_name
        , resolution_type
        , resolution_notes
        , string_agg(message_text, ' ') AS conversation_text
        from cte_obt
        where issue_resolved
        group by 1,2,3,4,5
    """).df()

df["doc"] = (
"Product: " + df["product_name"].fillna("") +
" Issue: " + df["issue_type"].fillna("") +
" Conversation: " + df["conversation_text"].fillna("") +
" Resolution: " + df["resolution_type"].fillna("")
)

vectorizer = TfidfVectorizer(stop_words="english")
matrix = vectorizer.fit_transform(df["doc"])


def retrieve_similar_tickets(open_ticket_text, top_k=3):
    q = vectorizer.transform([open_ticket_text])
    scores = cosine_similarity(q, matrix).flatten()
    idx = scores.argsort()[::-1][:top_k]

    return df.iloc[idx][
        [
            "conversation_key",
            "issue_type",
            "product_name",
            "resolution_type",
            "conversation_text"
        ]
    ]
   
def ask_chatbot(open_ticket_text):
    similar = retrieve_similar_tickets(open_ticket_text)

    context = ""

    for _, row in similar.iterrows():
        context += f"""
Resolved Ticket
Issue Type: {row.issue_type}
Product: {row.product_name}
Conversation: {row.conversation_text}
Resolution: {row.resolution_type}

"""

    prompt = f"""
You are an Eight Sleep support assistant.

Use ONLY the resolved tickets below.

Open Ticket:
{open_ticket_text}

Resolved Tickets:
{context}

Return:
1. Likely cause
2. Resolution steps
3. Escalate if needed
"""
    # print(prompt)
    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=prompt
    )

    return response.text

# response = ask_chatbot("Pod isn't cooling properly. Set to -10 but barely feels different.")
# print(response)

while True:
    ticket = input("Open Ticket > ").strip()

    if ticket.lower() in ["exit", "quit"]:
        break

    answer = ask_chatbot(ticket)

    print(f"\n {answer}")
    print("\n" + "-" * 80 + "\n")