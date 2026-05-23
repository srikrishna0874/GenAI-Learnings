from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.tools import tool

from langchain_community.utilities import GoogleSerperAPIWrapper
from langgraph.checkpoint.memory import MemorySaver

search = GoogleSerperAPIWrapper()

@tool
def search_tool(query: str) -> str:
    """
        Search the query on google and return the results.
        Args:
            query (str): The query to search on google.
    """
    
    return search.run(query)


from langchain.agents import create_agent

model = ChatGroq(model="openai/gpt-oss-20b")    

agent = create_agent(
    model = model,
    tools = [search_tool],
    system_prompt = "You are an agent and can search any question on google.",
    checkpointer=MemorySaver()
)

while True:
    query = input("User: ")
    if query.lower() in ["exit", "quit", "bye"]:
        print("Goodbye!")
        break
    
    response = agent.invoke(
        {"messages" : [{"role" : "user", "content" : query}]},
        {"configurable":{ "thread_id" : "1"}}
    )
    
    print("AI:" + response["messages"][-1].content)
    
