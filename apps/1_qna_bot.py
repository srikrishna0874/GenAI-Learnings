from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")


st.title("AskBuddy - Your Personal Q&A Bot")
st.markdown("AskBuddy is a simple Q&A bot built using LangChain and Google Gemini. Ask it anything!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    st.chat_message(message["role"]).markdown(message["content"])
    
query = st.chat_input("Type your question here...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    
    st.chat_message("user").markdown(query)
    with st.spinner("Thinking..."):
        response = model.invoke(query)
    st.chat_message("assistant").markdown(response.content)
    
    st.session_state.messages.append({"role": "assistant", "content": response.content})