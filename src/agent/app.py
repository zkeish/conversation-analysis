import os

import duckdb
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
import pandas as pd
from rich.console import Console

load_dotenv()

ENV = os.getenv('ENV', 'dev')
WORKING_DIR = os.getenv('WORKING_DIR', os.getcwd())

CLIENT = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

class SleepGenie:

    DATABASE = os.path.join(WORKING_DIR, f'pipelines/duckdb/{ENV}.duckdb')

    def generate_vector(self, text: str) -> list[float] | None:
        response = CLIENT.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768)
        )
        if response.embeddings:
            return response.embeddings[0].values
        else:
            raise Exception('Embedding not found!')

    def connect_db(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.DATABASE)
    
    def pull_context_table(self, conversation_text) -> tuple[str, list[int]]:
        context = ""
        with self.connect_db() as con:
            vector = self.generate_vector(conversation_text)
            # vector = [i for i in range(1,769)] # For testing
            df = con.execute("""select * ,array_cosine_similarity(embedding, ?::float[768]) as score from cx.mtc_cx_resolved order by score desc limit 3""", [vector]).df()
            keys = []
            for _, row in df.iterrows():
                conversation_key = row.conversation_key
                issue_type = row.issue_type
                product_name = row.product_name
                resolution_type = row.resolution_type
                resolution_notes = row.resolution_notes
                conversation_text = row.conversation_text
                keys.append(conversation_key)
                context += f"""
Resolved Ticket
Issue Type: {issue_type}
Product: {product_name}
Conversation: {conversation_text}
Resolution: {resolution_type}
"""
            return context, keys


    def ask_chatbot(self, conversation_text) -> str | None:
        context, keys = self.pull_context_table(conversation_text)
        keys_str = str(keys)
        prompt = f"""
You are an Eight Sleep CX Support Copilot.

Your goal is to help resolve the customer’s issue using prior resolved tickets as guidance.

---------------------
HOW TO THINK
---------------------
- Focus on the actual technical problem, not tone or emotion.
- Customers may use sarcasm, exaggeration, or frustration — ignore that and extract the real issue.
- If previous agents in the conversation gave incorrect or temporary fixes, do not rely on them.
- Look for consistent patterns across the resolved tickets rather than copying a single example.

---------------------
HOW TO USE THE DATA
---------------------
- Use the resolved tickets as your primary source of truth.
- Prioritize resolution notes over raw conversation text.
- If multiple tickets suggest the same fix, that is likely the correct path.
- If the tickets are unclear or conflicting, say so and suggest escalation.

---------------------
BEFORE YOU RESPOND
---------------------
- Check double check your response has solid resoning based on facts
- If you do not feel confident with your answer communicate that and recommend escalation

---------------------
HOW TO RESPOND
---------------------
Write a clear, structured answer with:

1. Likely cause  
2. Recommended steps to resolve (numbered)  
3. When to escalate (if needed)  
4. Confidence level (low, medium, high)
5. Resoning (how you got to this resolution)

Keep it concise, practical, and easy for a support agent to use.
Do not mention “retrieved tickets” or “context”.

---------------------
INPUT
---------------------

Open Ticket:
{conversation_text}

Resolved Tickets:
{context}
"""
        response = CLIENT.models.generate_content(model="gemma-4-31b-it", contents=prompt)
        return f"""{response.text} \n
conversation_keys used: {keys_str}
"""

    def main(self) -> None:
        console = Console(width=80)
        while True:
            ticket = input("Open Ticket > ").strip()

            if ticket.lower() in ["exit", "quit"]:
                break

            answer = self.ask_chatbot(ticket)
            console.print(f"\n {answer}")
            print("\n" + "-" * 80 + "\n")


if __name__ == "__main__":
    SleepGenie().main()

