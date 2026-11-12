"""
Streamlit UI for the SQL Server data agent.

Run from the project folder (with myvenv activated):
    streamlit run streamlit_app.py

Uses the same model, tools and system prompt as data_agent.py.
data_agent.py is not imported because it starts an input() loop on import.
"""

import json
import os
import uuid
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from agent_tools import execute_query, get_schema

load_dotenv()

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
MODEL_NAME = "openai/gpt-oss-120b"
BASE_URL = "https://api.groq.com/openai/v1"
SYSTEM_PROMPT = (
    "you are a SQL Server (T-SQL) expert. "
    "use tools if required to answer the user question."
)

# Chat history is saved next to this file so it survives page refreshes/restarts
HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "chat_history.json"
)

st.set_page_config(page_title="AI Data Agent", page_icon="🗄️", layout="wide")

# Make sidebar buttons full width and left-aligned (chat list look)
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] [data-testid="stButton"],
    section[data-testid="stSidebar"] [data-testid="stButton"] > div {
        width: 100%;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] button {
        width: 100%;
        justify-content: flex-start;
        text-align: left;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    /* delete icon buttons: centered, compact */
    section[data-testid="stSidebar"] [class*="st-key-delete_"] button {
        justify-content: center;
        padding-left: 0;
        padding-right: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Agent
# ----------------------------------------------------------------------------
@st.cache_resource
def get_agent():
    client = ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL)
    return create_agent(
        model=client,
        tools=[execute_query, get_schema],
        system_prompt=SYSTEM_PROMPT,
    )


def message_text(msg):
    """Return the plain text of a LangChain message (content may be str or blocks)."""
    content = msg.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, dict):
            parts.append(block.get("text", ""))
        else:
            parts.append(str(block))
    return "".join(parts)


def run_agent(history):
    """
    Send the conversation to the agent.
    Returns (final_answer, tool_calls) where tool_calls is a list of
    {"name", "args", "result"} dicts in the order they were made.
    """
    lc_messages = []
    for m in history:
        if m.get("error"):
            continue  # don't feed error messages back to the model
        if m["role"] == "user":
            lc_messages.append(HumanMessage(m["content"]))
        else:
            lc_messages.append(AIMessage(m["content"]))

    result = get_agent().invoke({"messages": lc_messages})
    new_messages = result["messages"][len(lc_messages):]

    calls = {}  # tool_call_id -> call info (dict keeps insertion order)
    for msg in new_messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                calls[tc["id"]] = {
                    "name": tc["name"],
                    "args": tc.get("args", {}),
                    "result": None,
                }
        elif isinstance(msg, ToolMessage):
            if msg.tool_call_id in calls:
                calls[msg.tool_call_id]["result"] = message_text(msg)

    answer = message_text(result["messages"][-1])
    return answer, list(calls.values())


# ----------------------------------------------------------------------------
# History persistence
# ----------------------------------------------------------------------------
def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.conversations, f, indent=2, default=str)
    except OSError as e:
        st.toast(f"Could not save chat history: {e}")


def now():
    return datetime.now().isoformat(timespec="seconds")


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
if "conversations" not in st.session_state:
    st.session_state.conversations = load_history()
if "current_id" not in st.session_state:
    st.session_state.current_id = None


def new_chat():
    st.session_state.current_id = None


def select_chat(cid):
    st.session_state.current_id = cid


def delete_chat(cid):
    st.session_state.conversations.pop(cid, None)
    if st.session_state.current_id == cid:
        st.session_state.current_id = None
    save_history()


def clear_all():
    st.session_state.conversations = {}
    st.session_state.current_id = None
    save_history()


# ----------------------------------------------------------------------------
# Rendering helpers
# ----------------------------------------------------------------------------
def render_tool_calls(tool_calls):
    for i, tc in enumerate(tool_calls, start=1):
        with st.expander(f"🔧 Tool call {i}: `{tc['name']}`", expanded=False):
            st.markdown("**Arguments**")
            args = tc.get("args") or {}
            if not args:
                st.caption("No arguments")
            for key, value in args.items():
                st.caption(key)
                if isinstance(value, str):
                    st.code(value, language="sql" if key == "query" else None)
                else:
                    st.code(json.dumps(value, indent=2, default=str), language="json")

            st.markdown("**Result**")
            result = tc.get("result")
            if result is None:
                st.caption("No result returned")
            else:
                st.code(result, language=None)


def render_message(m, show_tools):
    with st.chat_message(m["role"]):
        if m["role"] == "assistant" and show_tools and m.get("tool_calls"):
            render_tool_calls(m["tool_calls"])
        if m.get("error"):
            st.error(m["content"])
        else:
            st.markdown(m["content"])


# ----------------------------------------------------------------------------
# Sidebar: new chat, tool-call toggle, chat history
# ----------------------------------------------------------------------------
with st.sidebar:
    st.title("🗄️ AI Data Agent")

    st.button("➕ New chat", on_click=new_chat, type="primary")

    show_tools = st.toggle(
        "Show tool calls",
        value=True,
        key="show_tools",
        help="Show each tool the agent called, with its arguments and result",
    )

    st.divider()
    st.subheader("Chat history")

    conversations = st.session_state.conversations
    ordered = sorted(
        conversations.items(), key=lambda kv: kv[1].get("updated", ""), reverse=True
    )

    if not ordered:
        st.caption("No conversations yet.")

    for cid, conv in ordered:
        col_title, col_delete = st.columns([0.8, 0.2], gap="small")
        is_current = cid == st.session_state.current_id
        col_title.button(
            ("💬 " if is_current else "") + conv.get("title", "Untitled"),
            key=f"open_{cid}",
            on_click=select_chat,
            args=(cid,),
            type="secondary",
            disabled=is_current,
            help=conv.get("updated", ""),
        )
        col_delete.button(
            "🗑",
            key=f"delete_{cid}",
            on_click=delete_chat,
            args=(cid,),
            help="Delete this chat",
        )

    if ordered:
        st.divider()
        st.button("Clear all history", on_click=clear_all)


# ----------------------------------------------------------------------------
# Main chat area
# ----------------------------------------------------------------------------
current_id = st.session_state.current_id
current = conversations.get(current_id) if current_id else None
messages = current["messages"] if current else []

if not messages:
    st.title("Ask your SSMS database")
    st.caption(
        "e.g. *top 5 products by sales*, *what tables do I have?*, "
        "*monthly order count for 2024*"
    )

for m in messages:
    render_message(m, show_tools)

prompt = st.chat_input("Ask a question about your data...")

if prompt:
    # Create the conversation on the first message
    if current is None:
        current_id = str(uuid.uuid4())
        title = prompt.strip().replace("\n", " ")
        current = {
            "title": title[:40] + ("…" if len(title) > 40 else ""),
            "created": now(),
            "updated": now(),
            "messages": [],
        }
        conversations[current_id] = current
        st.session_state.current_id = current_id

    user_msg = {"role": "user", "content": prompt}
    current["messages"].append(user_msg)
    render_message(user_msg, show_tools)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer, tool_calls = run_agent(current["messages"])
                assistant_msg = {
                    "role": "assistant",
                    "content": answer,
                    "tool_calls": tool_calls,
                }
            except Exception as e:  # show the error in the chat instead of crashing
                assistant_msg = {
                    "role": "assistant",
                    "content": f"Error: {e}",
                    "tool_calls": [],
                    "error": True,
                }

    current["messages"].append(assistant_msg)
    current["updated"] = now()
    save_history()
    st.rerun()  # redraw so the sidebar and the new answer show up
