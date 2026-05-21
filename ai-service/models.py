from pydantic import BaseModel

class ChatRequest(BaseModel):
    subject: str
    grade: str
    chapter: str
    question: str

class UploadRequest(BaseModel):
    subject: str
    grade: str
    chapter: str
    file_path: str