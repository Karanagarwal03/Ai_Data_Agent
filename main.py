
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
# from langchain.messages import HumanMessage, AIMessage\
from agent_tools import execute_query,get_schema

load_dotenv()

client = ChatOpenAI(
    model="openai/gpt-oss-120b",
    base_url="https://api.groq.com/openai/v1"
)

# conversations = []
schema = get_schema.invoke({})




while True:
    user_input = input("Enter your query: ")
    if user_input.lower() == "exit":
        break
    prompt = f"""
        give me a SQL Server (T-SQL) compatible SQL query for the given question using given schema. Give me only the SQL query.
        question: {user_input}
        schema: {schema}
    """
    
    # conversations.append( HumanMessage(user_input))
    # response = client.invoke(input=conversations)
    response = client.invoke(input=prompt)
    # conversations.append( AIMessage(response.text))
    print(response.text)
    result = execute_query.invoke({"query": response.text})
    print(result)


# print(conversations)