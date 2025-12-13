from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
from app.config import settings

# Initialize Gemini Models
# "models/embedding-001" is the standard text embedding model
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=settings.GOOGLE_API_KEY)


chat_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GOOGLE_API_KEY)

def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.replace("\x00", "").replace("\u0000", "").strip()


def process_pdf_for_rag(file_path: str):
    # 1. Load PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    # 3. Generate Summary & Topics (using the first 3000 chars)
    # Gemini has a huge context window, so we can actually pass more text if needed.
    # full_text = " ".join([d.page_content for d in splits[:5]]) 
    full_text = " ".join(
    [clean_text(d.page_content) for d in splits[:5] if clean_text(d.page_content)]
    )

    
    summary_prompt = f"Summarize this research paper in 3 sentences: {full_text[:5000]}"
    summary = chat_model.invoke(summary_prompt).content
    
    topics_prompt = f"Extract 5 main technical keywords from this text as a comma-separated list: {full_text[:5000]}"
    topics_str = chat_model.invoke(topics_prompt).content
    topics = [t.strip() for t in topics_str.split(",")]
    
    # 4. Create Embeddings
    vectors = []
    # Note: embed_documents is faster than loop, but for clarity in this MVP loop is fine
    # For production speed, use: embeddings_model.embed_documents([s.page_content for s in splits])
    # for split in splits:
    #     vector = embeddings_model.embed_query(split.page_content)
    #     vectors.append({
    #         "content": split.page_content,
    #         "vector": vector
    #     })

    for split in splits:
        content = clean_text(split.page_content)

        if not content or len(content) < 20:
            continue

        vector = embeddings_model.embed_query(content)
        vectors.append({
            "content": content,
            "vector": vector
        })

        
    return summary, topics, vectors