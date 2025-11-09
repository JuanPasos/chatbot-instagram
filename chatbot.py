# chatbot.py
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

DB_PATH = "chroma_db"
MODEL_NAME = "llama3.2"
DOCS_FOLDER = "docs"

def load_documents():
    docs = []
    if not os.path.exists(DOCS_FOLDER):
        os.makedirs(DOCS_FOLDER)
        return docs
    for file in os.listdir(DOCS_FOLDER):
        path = os.path.join(DOCS_FOLDER, file)
        if file.endswith(".pdf"):
            docs.extend(PyPDFLoader(path).load())
        elif file.endswith(".txt"):
            docs.extend(TextLoader(path, encoding="utf-8").load())
    return docs

def get_retriever():
    embeddings = OllamaEmbeddings(model=MODEL_NAME)
    if os.path.exists(DB_PATH):
        return Chroma(persist_directory=DB_PATH, embedding_function=embeddings).as_retriever()
    docs = load_documents()
    if not docs:
        return None
    splits = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=DB_PATH)
    return vectorstore.as_retriever(search_kwargs={"k": 4})

prompt = ChatPromptTemplate.from_template(
    "Responde SOLO con base en el contexto. Si no sabes, di: 'No tengo esa info.'\n\nContexto: {context}\nPregunta: {question}"
)

def chatbot(question):
    retriever = get_retriever()
    if not retriever:
        return "No hay documentos en /docs"
    llm = ChatOllama(model=MODEL_NAME, temperature=0.3)
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt | llm | StrOutputParser()
    )
    return chain.invoke(question)