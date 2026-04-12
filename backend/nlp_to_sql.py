import sqlite3
import pandas as pd
from backend.groq_llm import GroqFormatter

class NLPToSQL:
    def __init__(self, api_key: str):
        self.db_conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.llm = GroqFormatter(api_key=api_key)

    def load_csv(self, file_path: str, table_name: str = "uploaded_data") -> str:
        try:
            df = pd.read_csv(file_path)
            df.to_sql(table_name, self.db_conn, if_exists="replace", index=False)
            return f"Successfully loaded CSV into table '{table_name}' with {len(df)} rows."
        except Exception as e:
            return f"Error loading CSV: {str(e)}"

    def get_schema(self) -> str:
        query = "SELECT sql FROM sqlite_master WHERE type='table';"
        cursor = self.db_conn.cursor()
        cursor.execute(query)
        schemas = cursor.fetchall()
        if not schemas:
            return "No tables available."
        return "\n".join([s[0] for s in schemas if s[0]])

    def query(self, nl_query: str) -> dict:
        schema = self.get_schema()
        if schema == "No tables available.":
            return {"error": "Please upload a CSV file first before asking a data question."}

        # Ask LLM to generate SQL
        sql_query = self.llm.generate_sql(nl_query, schema)
        
        # Clean the generated string (remove markdown if any, though system prompt forbids it)
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        try:
            cursor = self.db_conn.cursor()
            cursor.execute(sql_query)
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            return {
                "sql": sql_query,
                "columns": columns,
                "data": results
            }
        except Exception as e:
            # Maybe the LLM got it wrong
            return {"error": f"Failed to execute SQL: {sql_query}\nError: {str(e)}"}
