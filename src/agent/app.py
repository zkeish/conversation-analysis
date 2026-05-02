import os

import duckdb
from dotenv import load_dotenv
import google.genai as genai
import pandas as pd

load_dotenv()

ENV = os.getenv('ENV', 'dev')
WORKING_DIR = os.getenv('WORKING_DIR', os.getcwd())

CLIENT = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

class SleepGenie:

    DATABASE = os.path.join(WORKING_DIR, f'pipelines/duckdb/{ENV}.duckdb')

    def connect_db(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.DATABASE)
    
    def pull_context_table(self, conversation_text) -> str:
        context = ""
        with self.connect_db() as con:
            # vector = self.generate_vector(conversation_text)
            vector = [i for i in range(1,769)]
            df = con.execute("""select * ,array_cosine_similarity(embedding, ?::float[768]) as score from cx.mtc_cx_resolved order by score desc limit 3""", [vector]).df()
            for _, row in df.iterrows():
                conversation_key = row.conversation_key
                issue_type = row.issue_type
                product_name = row.product_name
                resolution_type = row.resolution_type
                resolution_notes = row.resolution_notes
                conversation_text = row.conversation_text
                context += f"""
Resolved Ticket
Issue Type: {issue_type}
Product: {product_name}
Conversation: {conversation_text}
Resolution: {resolution_type}
"""
            return context


    def ask_chatbot(self, conversation_text) -> str | None:
        context = self.pull_context_table(conversation_text)

        prompt = f"""
You are an Eight Sleep support assistant.

Use ONLY the resolved tickets below.

Open Ticket:
{conversation_text}

Resolved Tickets:
{context}

Return:
1. Likely cause
2. Resolution steps
3. Escalate if needed
"""
        # print(prompt)
        response = CLIENT.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt
        )

        return response.text

    def main(self) -> None:

        while True:
            ticket = input("Open Ticket > ").strip()

            if ticket.lower() in ["exit", "quit"]:
                break

            answer = self.ask_chatbot(ticket)

            print(f"\n {answer}")
            print("\n" + "-" * 80 + "\n")


if __name__ == "__main__":
    SleepGenie().main()

