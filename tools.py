# import psycopg
# import pandas as pd
# from sqlalchemy import create_engine

# #postgresql+psycopg://USERNAME:PASSWORD@HOST:PORT/DATABASE

# engine = create_engine(
# "postgresql+psycopg://postgres@localhost:5432/retail"
# )

# def execute_query(query):
# with engine.connect() as conn:
# df = pd.read_sql(query, conn)

# return df

import os
import re
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

# oracle+oracledb://USERNAME:PASSWORD@HOST:PORT/SID
url = URL.create(
    "oracle+oracledb",
    username="system",
    password=os.getenv("ORACLE_PASSWORD"),
    host="localhost",
    port=1521,
    database="orcl",          # your SID from SQL Developer
)

engine = create_engine(url)


def clean_sql(query):
    # remove ```sql fences from the LLM output and the trailing semicolon
    query = re.sub(r"```(?:sql)?", "", query, flags=re.IGNORECASE)
    return query.strip().rstrip(";")


def execute_query(query):
    query = clean_sql(query)
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df.to_string(index=False)  # Convert DataFrame to string for printing


    
# print(execute_query("SELECT order_id, order_date FROM orders FETCH FIRST 5 ROWS ONLY"))

# print(execute_query("SELECT * from emp"))