from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import PyPDFLoader, PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
import streamlit as st

# data in session for streamlit

if "is_document_uploaded" not in st.session_state:
    st.session_state.is_document_uploaded = False

if "agent" not in st.session_state:
    st.session_state.agent = None

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "messages_history" not in st.session_state:
    st.session_state.messages_history = []


def process_document(path: str):

    # load pdf
    pdfLoader = PyPDFDirectoryLoader(path)
    docs = pdfLoader.load()

    # split the document into smaller chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents(docs)

    # define embeddiings model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # create vector database from the documents and embeddings
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
    )

    llm = ChatGroq(model="openai/gpt-oss-20b")

    @tool
    def retrieve_context(query: str) -> str:
        """Tool for retrieving relevant context from the knowledge database."""
        results = vectordb.similarity_search(query, k=4)
        return "\n\n".join([result.page_content for result in results])

    system_prompt = """
        You are a helpful AI assistant answering questions from uploaded PDFs.

        IMPORTANT RULES:
        - ALWAYS use the retrieve_context tool before answering.
        - Answers must ONLY be based on retrieved context.
        - Multiple PDFs may be uploaded.
        - If information comes from multiple documents, combine them properly.
        - If answer is not found in context, say so.
    """

    memory_saver = InMemorySaver()

    agent = create_agent(
        model=llm,
        tools=[retrieve_context],
        system_prompt=system_prompt,
        checkpointer=memory_saver,
    )

    st.session_state.agent = agent
    st.session_state.is_document_uploaded = True


### Upload UI
if not st.session_state.is_document_uploaded:
    uploaded = st.file_uploader(
        label="Select Files", accept_multiple_files=True, type=["pdf"]
    )

    if uploaded:
        with st.spinner("Processing..."):
            path = "./doc_files/"

            for file in uploaded:
                print(file.name)
                with open(path + file.name, "wb") as f:
                    f.write(file.getvalue())

            process_document(path)
            st.rerun()


### Chat UI
if st.session_state.is_document_uploaded and st.session_state.agent:

    for message in st.session_state.messages_history:
        role = message.get("role")
        content = message.get("content")

        st.chat_message(role).markdown(content)

    query = st.chat_input("Ask anything related to uploaded documents...")

    if query:
        st.session_state.messages_history.append({"role": "user", "content": query})
        st.chat_message("user").markdown(query)

        response = st.session_state.agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            {"configurable": {"thread_id": 1}},
        )

        result = response["messages"][-1].content
        st.chat_message("ai").markdown(result)
        st.session_state.messages_history.append({"role": "ai", "content": result})
