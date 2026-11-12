
import os
import re
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from langchain.tools import tool

load_dotenv()

# oracle+oracledb://USERNAME:PASSWORD@HOST:PORT/SID
url = URL.create(
    "mssql+pyodbc",
    host="localhost\\SQLEXPRESS",
    database="retail",
    query={"driver": "ODBC Driver 17 for SQL Server", "trusted_connection": "yes"},
)

engine = create_engine(url)


def clean_sql(query):
    # remove ```sql fences from the LLM output and the trailing semicolon
    query = re.sub(r"```(?:sql)?", "", query, flags=re.IGNORECASE)
    return query.strip().rstrip(";")

#DECORATORS
@tool
def execute_query(query):
    #DOCSTRING
    """"
    use this tool to run a select query and get the result 
    """
    query = clean_sql(query)
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df.to_string(index=False)  # Convert DataFrame to string for printing

#DECORATORS
@tool
def get_schema():
    #DOCSTRING
    """"
    use this tool to get the schema of all the tables from the database  
    """
    query = f"""
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df.to_string(index=False)  # Convert DataFrame to string for printing                                                 
# print(execute_query("SELECT order_id, order_date FROM orders FETCH FIRST 5 ROWS ONLY"))

# print(execute_query("SELECT * from emp"))
# print (get_schema())