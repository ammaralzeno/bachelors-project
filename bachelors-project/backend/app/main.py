import os
from fastapi import FastAPI, UploadFile, File
from app.parsers.pdfParser import extract_sections_and_subsections
from app.parsers.pdf2docx import convert_pdf_to_docx
from app.parsers.pdfParserElias import extract_everything
import shutil
from app.llm import process_sections
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
import io
import asyncio
from app.parsers.docxParser import extract_sections_from_docx

app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "FastAPI Backend is Running!"}


UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  


@app.post("/analyze-pdf/")
async def analyze_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename) 

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse the file to get subsections
    subsections = extract_sections_and_subsections(file_path)
    
    # Process all sections in parallel using the predefined criteria
    matching_sections = await process_sections(subsections)
    
    return {"matching_sections": matching_sections}



# Elias -----------------------------------------------

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename) 

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse the file
    subsections = extract_sections_and_subsections(file_path)
    
    return {"subsections": subsections}




@app.post("/everything-scraper/")
async def upload_p(file: UploadFile = File(...)):
    """
    Uploads a PDF file, extracts all structured content (sections, subsections, text, and tables),
    and returns the extracted data as a JSON response.
    """
    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process the PDF and extract structured content
    extracted_data = extract_everything(file_path)

    return extracted_data







# AMMAR -----------------------------------------------


@app.post("/convert-pdf-to-docx/")
async def convert_pdf_to_docx_endpoint(file: UploadFile = File(...)):
    """
    Converts a PDF file to DOCX format and returns the converted file for download.
    """
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Convert PDF to DOCX
        docx_path = convert_pdf_to_docx(file_path)
        
        # Return the converted file
        return FileResponse(
            path=docx_path,
            filename=os.path.basename(docx_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Conversion failed: {str(e)}"}
        )

@app.post("/llm-pdf-analysis/")
async def llm_pdf_analysis(file: UploadFile = File(...)):
    """
    Analyzes a PDF using LLM to process each page and extract relevant sections.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename) 

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Use the LLM-based parser
    from app.parsers.llm_parse import extract_sections_with_llm
    result = await extract_sections_with_llm(file_path)
    
    return result

@app.post("/parse-docx/")
async def parse_docx(file: UploadFile = File(...)):
    """
    Parses a DOCX file and extracts sections, subsections, and their content.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Parse the DOCX file
    extracted_data = extract_sections_from_docx(file_path)
    
    return JSONResponse(content=extracted_data)

