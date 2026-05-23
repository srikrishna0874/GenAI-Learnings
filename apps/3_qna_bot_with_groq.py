from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
import streamlit as st


load_dotenv()

model = ChatGroq(model="openai/gpt-oss-20b")

search = GoogleSerperAPIWrapper()

@tool
def search_tool(query: str) -> str:
    """
        Search the query on google and return the results.
        Args:
            query (str): The query to search on google.
    """
    
    return search.run(query)

if "memory" not in st.session_state:
    st.session_state.memory = MemorySaver()
    st.session_state.history = []

st.subheader("QuickAnswer - Answers at the speed of thought")
    
for message in st.session_state.history:
    st.chat_message(message["role"]).markdown(message["content"])

agent = create_agent(
    model = model,
    tools = [search_tool],
    system_prompt = "You are an agent and can search any question on google.",
    checkpointer=st.session_state.memory
)



query = st.chat_input("Ask me anything...")

if query:
    st.chat_message("user").markdown(query)
    st.session_state.history.append({"role": "user", "content": query})
    
    response = agent.stream(
        {"messages" : [{"role" : "user", "content" : query}]},
        {"configurable":{ "thread_id" : "1"}},
        stream_mode="messages"
    )
    
    ai_container = st.chat_message("assistant")
    with ai_container:
        message = ''
        space = st.empty()
        
        for chunk in response:
            message += chunk[0].content
            
            space.write(message)
            
        st.session_state.history.append({"role": "assistant", "content": message})
        
