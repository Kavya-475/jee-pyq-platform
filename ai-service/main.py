import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google import genai
from qdrant_client import QdrantClient 
from dotenv import load_dotenv

from database import get_db, BookCache
from models import ChatRequest, UploadRequest

load_dotenv()

# This is the line your code was missing!
app = FastAPI(title="JEE AI Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI and Vector DB
client = genai.Client()
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)

@app.post("/internal/ai/chat")
def student_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    RAG STUDENT ROUTE: Searches Qdrant for the exact paragraphs needed,
    then uses Gemini to formulate the final answer.
    """
    
# 1. NEW: Check for missing context (Subject, Grade, Chapter)
    if not request.subject or not request.grade or not request.chapter:
        missing = []
        if not request.subject: missing.append("Subject")
        if not request.grade: missing.append("Class")
        if not request.chapter: missing.append("Chapter")
        
        # Make the AI point the user to the new Dropdown Options
        missing_str = " and ".join(missing)
        friendly_rejection = f"I would love to help you with that! But before I can search the textbooks, could you please select your **{missing_str}** from the dropdown options at the top of the screen?"
        
        return {"answer": friendly_rejection, "success": True}

    # 2. If all data is present, build the table name and proceed normally
    collection_name = f"{request.subject}_class_{request.grade}_v2".lower()
    
    try:
        # Turn the student's question into math (Vectors)
        print(f"🤔 Understanding question: {request.question}")
        question_vector = client.models.embed_content(
            model="gemini-embedding-001",
            contents=request.question,
        ).embeddings[0].values

        # Search Qdrant for the 5 most relevant textbook chunks
        print("🔍 Searching Vector Database...")
        search_response = qdrant_client.query_points(
            collection_name=collection_name,
            query=question_vector,
            limit=5  # Only grab the top 5 chunks
        )
        search_results = search_response.points

        if not search_results:
            return {"answer": "I couldn't find any relevant information in this chapter.", "success": True}

        # Stitch the 5 chunks of text together
        context_text = "\n\n---\n\n".join([hit.payload["text"] for hit in search_results])

        # Give the context and the question to Gemini
        print("🧠 Formulating answer...")
        prompt = f"""
        You are an expert JEE tutor. Use ONLY the following textbook excerpts to answer the student's question. 
        If the excerpts do not contain the answer, politely say you don't know based on this book.
        Strictly format math using LaTeX ($ and $$).

        TEXTBOOK EXCERPTS:
        {context_text}

        STUDENT QUESTION:
        {request.question}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return {"answer": response.text, "success": True}

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
