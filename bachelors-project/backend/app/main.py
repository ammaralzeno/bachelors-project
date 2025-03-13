import os
from fastapi import FastAPI, UploadFile, File
from app.pdfParser import extract_titles_from_pdf
import shutil

app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "FastAPI Backend is Running!"}


UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename) 

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse the file
    titles = extract_titles_from_pdf(file_path)
    
    return {"titles": titles}
