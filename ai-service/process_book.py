import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from google import genai
import uuid

# Load environment variables
load_dotenv()

# Initialize Clients
# Initialize Clients
gemini_client = genai.Client()
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60  # 👈 ADD THIS LINE
)

def extract_text_from_pdf(pdf_path):
    print(f"📄 Reading {pdf_path}...")
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text):
    print("✂️ Chopping text into 600-character chunks...")
    # Matches the exact requirements from your Disha architecture report
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        length_function=len,
    )
    return text_splitter.split_text(text)

def generate_embeddings_and_store(chunks, collection_name):
    print("🧠 Converting chunks to AI Vectors and sending to Qdrant...")
    
    # 1. Create the Qdrant Collection (Table) if it doesn't exist
    # Gemini embeddings are 768 dimensions
    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE), # 👈 CHANGE THIS TO 3072
        )

    # 2. Process and upload chunks in batches
    points = []
    for i, chunk in enumerate(chunks):
        # Ask Gemini to turn the text into numbers (vectors)
# Ask Gemini to turn the text into numbers (vectors)
        response = gemini_client.models.embed_content(
            model="gemini-embedding-001",  # 👈 UPDATE THIS LINE
            contents=chunk,
        )
        
        # Create a Qdrant point (ID, Vector, and the actual text payload)
        points.append(
            PointStruct(
                id=str(uuid.uuid4()), 
                vector=response.embeddings[0].values, 
                payload={"text": chunk} # We save the text so we can read it later!
            )
        )
        
        # Print progress
        if i % 10 == 0:
            print(f"Processed {i}/{len(chunks)} chunks...")

    # Upload to Qdrant Cloud
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )
    print(f"✅ Success! Uploaded {len(chunks)} chunks to Qdrant collection: {collection_name}")

# ==========================================
# EXECUTE THE SCRIPT
# ==========================================
if __name__ == "__main__":
    pdf_filename = "kinematics.pdf" 
    qdrant_table_name = "physics_class_11_kinematics_v2" # 👈 ADD _v2 HERE
    
    if os.path.exists(pdf_filename):
        raw_text = extract_text_from_pdf(pdf_filename)
        text_chunks = chunk_text(raw_text)
        generate_embeddings_and_store(text_chunks, qdrant_table_name)
    else:
        print(f"❌ Error: Could not find {pdf_filename} in the folder.")