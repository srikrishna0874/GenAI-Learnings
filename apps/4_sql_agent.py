from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
import os
from langchain.agents import create_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
import streamlit as st
from langgraph.checkpoint.memory import InMemorySaver
from system_prompts import system_prompt

load_dotenv()

model = ChatGroq(model="openai/gpt-oss-20b")

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)

db = SQLDatabase(engine)

toolkit = SQLDatabaseToolkit(db=db, llm=model)

tools = toolkit.get_tools()

system_prompt = system_prompt

@st.cache_resource
def get_sql_agent():
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=InMemorySaver(),
    )

    return agent


agent = get_sql_agent()

if "history" not in st.session_state:
    st.session_state.history = []

st.subheader("SQL Agent - Manage your tasks with natural language")

for message in st.session_state.history:
    st.chat_message(message["role"]).markdown(message["content"])

query = st.chat_input("Ask me anything related to your tasks...")

if query:
    st.chat_message("user").markdown(query)
    st.session_state.history.append({"role": "user", "content": query})

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
              
               response = agent.invoke(
                  {"messages": [{"role": "user", "content": query}]},
                  {"configurable": {"thread_id": "1"}},
               )
               result = response["messages"][-1].content
            except Exception as e:
                result = "Sorry, I couldn't process that request properly. Please try again."
                
            st.markdown(result)
            st.session_state.history.append({"role": "assistant", "content": result})
