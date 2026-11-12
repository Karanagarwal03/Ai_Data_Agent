# 🗄️ AI Data Agent

> **Talk to your SQL Server database in plain English.**
> Ask *"Which month had the highest sales?"* and an LLM agent inspects your schema, writes the T-SQL, runs it, and explains the answer, all in a chat UI.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-agents-1C3C3C)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![SQL Server](https://img.shields.io/badge/DB-SQL%20Server-CC2927?logo=microsoftsqlserver&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-gpt--oss--120b%20on%20Groq-orange)

---

## ✨ What it does

You type a question. The agent decides what to do:

1. 🔍 **Reads the schema** (`get_schema`) so it knows your tables and columns
2. ✍️ **Writes a T-SQL query** that fits that schema
3. ⚡ **Runs it** (`execute_query`) against SQL Server
4. 💬 **Explains the result** in plain language, with the SQL shown

### Example

> **You:** higest sales in which month ?
> **Agent:** The month with the highest total sales is **November**, with ≈ 352,461.10.
>
> **You:** which year of november and why?
> **Agent:** **November 2021** (118,447.85), ahead of 2020, 2018 and 2019, plus the SQL it used.

```sql
SELECT YEAR(order_date) AS sales_year, SUM(sales) AS total_sales
FROM orders
WHERE MONTH(order_date) = 11
GROUP BY YEAR(order_date)
ORDER BY total_sales DESC
```

It keeps conversation context, so follow-ups like *"and why?"* work.

---

## 🖥️ Features

- **Chat UI** built with Streamlit, with multiple conversations
- **Persistent history** saved to `chat_history.json` (survives restarts)
- **Transparent tool calls**: toggle to see every tool the agent called, its SQL arguments and raw results
- **Schema-aware agent** via LangChain `create_agent` (tool-calling loop)
- **Fast, cheap inference** using `openai/gpt-oss-120b` through Groq's OpenAI-compatible API
- **Error-tolerant**: failures show up in the chat instead of crashing the app
- Cleans LLM output (strips ```` ```sql ```` fences and trailing `;`) before running it

---

## 🧱 Architecture

```
          ┌────────────────────┐
          │  Streamlit chat UI │  streamlit_app.py
          └─────────┬──────────┘
                    │ messages
                    ▼
          ┌────────────────────┐        ┌────────────────────────┐
          │  LangChain agent   │ ─────▶ │ Groq · gpt-oss-120b    │
          │  (tool-calling)    │ ◀───── │ (OpenAI-compatible API)│
          └─────────┬──────────┘        └────────────────────────┘
                    │ calls
        ┌───────────┴───────────┐
        ▼                       ▼
  get_schema()           execute_query(sql)      agent_tools.py
        └───────────┬───────────┘
                    ▼
          ┌────────────────────┐
          │ SQL Server (retail)│  via SQLAlchemy + pyodbc
          └────────────────────┘
```

## 📁 Project structure

| File | Purpose |
|------|---------|
| `streamlit_app.py` | Streamlit chat UI, history sidebar, tool-call viewer |
| `agent_tools.py` | The two agent tools: `get_schema` and `execute_query`, plus the DB engine |
| `data_agent.py` | Same agent as a simple terminal chat loop |
| `main.py` | Minimal non-agent version: one prompt → SQL → run (good for learning) |
| `tools.py` | Early Oracle/Postgres prototype, kept for reference |
| `chat_history.json` | Saved conversations (auto-generated) |
| `.env` | Your API key (never commit this) |

---

## 🚀 Getting started

### Prerequisites

- Python 3.10+
- SQL Server (Express works) with a database named `retail`
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
- A free [Groq API key](https://console.groq.com/keys)

### 1. Clone & create a virtual environment

```bash
python -m venv myvenv
myvenv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install langchain langchain-openai python-dotenv sqlalchemy pyodbc pandas streamlit
```

### 3. Configure your API key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY="your_groq_api_key_here"
```

> The variable is named `OPENAI_API_KEY` because `langchain-openai` reads that name. The value is your **Groq** key.

### 4. Point it at your database

Edit the connection in `agent_tools.py` if your server differs:

```python
url = URL.create(
    "mssql+pyodbc",
    host="localhost\\SQLEXPRESS",
    database="retail",
    query={"driver": "ODBC Driver 17 for SQL Server", "trusted_connection": "yes"},
)
```

### 5. Run it

**Web UI:**

```bash
streamlit run streamlit_app.py
```

**Terminal agent:**

```bash
python data_agent.py
```

---

## 🗃️ Sample dataset

The demo uses a retail "Superstore"-style dataset with two tables:

- **`orders`**: `order_id`, `order_date`, `ship_date`, `ship_mode`, `customer_id`, `customer_name`, `segment`, `country`, `city`, `state`, `region`, `product_id`, `category`, `sub_category`, `product_name`, `sales`, `quantity`, `discount`, `profit`
- **`returns`**: `order_id`, `return_reason`

Try asking:

- *Top 5 products by sales*
- *Which region has the best profit margin?*
- *Monthly order count for 2021*
- *What are the most common return reasons?*
- *What tables do I have?*

---

## 🔒 Safety notes

- The agent can run **any SQL the model writes**. Connect with a **read-only** database user for anything beyond local experiments.
- Never commit `.env` or `chat_history.json` (it can contain query results). Both are listed in `.gitignore`.
- Windows Authentication (`trusted_connection=yes`) means queries run as your Windows user.

## 🛣️ Ideas for next steps

- [ ] Block non-`SELECT` statements in `execute_query`
- [ ] Auto-render charts for numeric results
- [ ] CSV export of query results
- [ ] Row limits and query timeouts
- [ ] Move DB host/name into `.env`

---

## 🛠️ Tech stack

LangChain · Streamlit · SQLAlchemy · pyodbc · pandas · Groq (`openai/gpt-oss-120b`) · SQL Server

Made with ☕ by Karan
