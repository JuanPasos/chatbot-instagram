# chatbot.py - RAG con Ollama en Railway + Tus PDF
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
import logging

# === CONFIGURACIÓN OLLAMA EN RAILWAY ===
OLLAMA_URL = "https://ollama-production-cc3a.up.railway.app"  # ← TU URL
MODEL_NAME = "llama3.2"
DB_PATH = "/tmp/chroma_db"  # Disco temporal en Render

# === LOGS PARA DEBUG (OPCIONAL) ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === CARGA Y PROCESA TUS DOCUMENTOS (PDF/TXT) ===
def load_documents():
    docs = []
    docs_folder = "docs"
    if not os.path.exists(docs_folder):
        logger.warning("Carpeta 'docs/' no encontrada. Crea y sube tus PDF/TXT.")
        return docs

    for file in os.listdir(docs_folder):
        path = os.path.join(docs_folder, file)
        try:
            if file.lower().endswith(".pdf"):
                loader = PyPDFLoader(path)
                docs.extend(loader.load())
                logger.info(f"PDF cargado: {file}")
            elif file.lower().endswith((".txt", ".md")):
                loader = TextLoader(path, encoding="utf-8")
                docs.extend(loader.load())
                logger.info(f"TXT cargado: {file}")
        except Exception as e:
            logger.error(f"Error cargando {file}: {e}")
    return docs

# === CREA O CARGA LA BASE DE CONOCIMIENTO (Chroma) ===
def get_retriever():
    embeddings = OllamaEmbeddings(model=MODEL_NAME, base_url=OLLAMA_URL)

    # Si ya existe la base de datos, cárgala
    if os.path.exists(DB_PATH):
        logger.info("Cargando base de conocimiento existente...")
        return Chroma(persist_directory=DB_PATH, embedding_function=embeddings).as_retriever(search_kwargs={"k": 4})

    # Si no, crea una nueva
    docs = load_documents()
    if not docs:
        logger.warning("No hay documentos para procesar.")
        return None

    logger.info(f"Procesando {len(docs)} documentos...")
    splits = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    logger.info("Base de conocimiento creada y guardada.")
    return vectorstore.as_retriever(search_kwargs={"k": 4})

# === PROMPT DE RESPUESTA ===
prompt = ChatPromptTemplate.from_template(
    "Responde SOLO con base en el contexto. Si no sabes, di: 'No tengo esa información.'\n\n"
    "Contexto:\n{context}\n\n"
    "Pregunta: {question}"
)

# === FUNCIÓN PRINCIPAL DEL BOT ===
def chatbot(question: str) -> str:
    logger.info(f"Pregunta recibida: {question}")

    retriever = get_retriever()
    if not retriever:
        return "No hay documentos en la carpeta /docs. Sube tus PDF/TXT en Render."

    llm = ChatOllama(model=MODEL_NAME, base_url=OLLAMA_URL, temperature=0.3)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Cadena RAG completa
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    try:
        response = chain.invoke(question)
        logger.info("Respuesta generada con éxito.")
        return response
    except Exception as e:
        logger.error(f"Error en RAG: {e}")
        return "Lo siento, hubo un error al procesar tu pregunta."
