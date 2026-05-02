import os

import duckdb
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
import pandas as pd

load_dotenv()

ENV = os.getenv('ENV', 'dev')
WORKING_DIR = os.getenv('WORKING_DIR', os.getcwd())

CLIENT = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

class VectorDB:

    DATABASE = os.path.join(WORKING_DIR, f'pipelines/duckdb/{ENV}.duckdb')

    def generate_vector(self, text: str) -> list[float] | None:
        """Generate a vector embedding for the given text using Gemini API.
        
        Args:
            text: The input text to embed.
            
        Returns:
            A list of 768 float values representing the text embedding.
            
        Raises:
            Exception: If the API fails to generate an embedding.
        """
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
        """Establish a connection to the DuckDB database.
        
        Returns:
            A DuckDBPyConnection object connected to the configured database.
        """
        return duckdb.connect(self.DATABASE)
    
    def load_vss(self) -> None:
        """Install and load the DuckDB Vector Similarity Search (VSS) extension.
        
        This extension is required for efficient vector similarity operations.
        """
        with self.connect_db() as con:
            con.sql('INSTALL vss;')
            con.sql('LOAD vss;')

    def embed_vector(self, limit: int | None=1500) -> None:
        """Generate and store vector embeddings for conversations without embeddings.
        
        Retrieves conversations from the database that don't have embeddings yet,
        generates embeddings for their text, and updates the database with the results.
        
        Args:
            limit: Maximum number of conversations to embed. Defaults to 1500.
        """
        with self.connect_db() as con:
            df = con.execute(f"select * from cx.mtc_cx_resolved where embedding is null limit ?", [limit]).df()
            if not df.empty:
                for i, row in df.iterrows():
                    conversation_key = row.conversation_key
                    conversation_text = row.conversation_text
                    print(conversation_key)
                    vector = self.generate_vector(conversation_text)
                    # vector = [i for i in range(1,769)] # For testing
                    con.execute(f"update cx.mtc_cx_resolved set embedding = ? where conversation_key = ?", [vector, conversation_key])

    def add_index(self) ->None:
        """Create an HNSW index on the embedding column for efficient similarity searches.
        
        This method is experimental and currently unused. It creates a Hierarchical 
        Navigable Small World (HNSW) index on the embedding column with cosine distance metric.
        """
        # Experimental so not going to use
        with self.connect_db() as con:
            con.sql('SET hnsw_enable_experimental_persistence = true')
            con.execute("create index idx on cx.mtc_cx_resolved using HNSW (embedding) with (metric = 'cosine')")
    
    def main(self):
        """Run the main embedding workflow.
        
        Loads the VSS extension and generates embeddings for conversations.
        """
        self.load_vss()
        self.embed_vector(limit=1500)

if __name__ == "__main__":
    VectorDB().main()
