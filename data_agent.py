
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from agent_tools import execute_query, get_schema
from langchain.agents import create_agent

load_dotenv()

tools = [execute_query, get_schema]

model = ChatOpenAI(model='openai/gpt-oss-120b', base_url='https://api.groq.com/openai/v1')

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="You are a SQL Server (T-SQL) expert. Use tools if required."
)

while True:
    user_input = input("ask question: ")

    if user_input == 'exit':
        break

    response = agent.invoke({'messages': [user_input]})
    print(response['messages'][-1].text)
