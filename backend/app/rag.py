from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
from app.config import settings
import io
from PyPDF2 import PdfReader
from langchain_core.documents import Document




embeddings_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=settings.GOOGLE_API_KEY)


chat_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GOOGLE_API_KEY)

def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.replace("\x00", "").replace("\u0000", "").strip()


def process_pdf_for_rag(pdf_bytes: bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))

    docs = []
    for page in reader.pages:
        text = clean_text(page.extract_text())
        if text:
            docs.append(Document(page_content=text))

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(docs)

    full_text = " ".join([d.page_content for d in splits[:5]])

    summary = chat_model.invoke(
        f"Summarize this research paper in 3 sentences: {full_text[:5000]}"
    ).content

    topics_str = chat_model.invoke(
        f"Extract 5 technical keywords: {full_text[:5000]}"
    ).content
    topics = [t.strip() for t in topics_str.split(",")]

    vectors = []
    for split in splits:
        vector = embeddings_model.embed_query(split.page_content)
        vectors.append({"content": split.page_content, "vector": vector})

    return summary, topics, vectors
