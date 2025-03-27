import os
from fastapi import FastAPI, UploadFile, File, Request
from app.parsers.pdfParser import extract_sections_and_subsections
from app.parsers.pdfParserElias import extract_everything
import shutil
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.step1.llm_sections import analyze_pdf_sections
from app.step2.parse_sections import parse_evaluation_components

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def read_root():
    return {"message": "FastAPI Backend is Running!"}


UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  


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

@app.post("/analyze-pdf-sections/")
async def analyze_pdf_sections_endpoint(file: UploadFile = File(...)):
    """
    Analyzes PDF sections using LLM to identify sections that match specific criteria.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename) 

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Parse the file to get subsections
        parsed_data = extract_everything(file_path)
        
        # Process sections to find those that match criteria
        analysis_results = await analyze_pdf_sections({"subsections": parsed_data})
        
        return analysis_results
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Analysis failed: {str(e)}"}
        )

@app.post("/parse-evaluation-components/")
async def parse_evaluation_components_endpoint(file: UploadFile = File(...)):
    """
    Full pipeline: parses PDF, analyzes sections, and extracts evaluation components in one step.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename) 

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Parse the file to get subsections
        parsed_data = extract_everything(file_path)
        
        # Process sections to find those that match criteria
        analysis_results = await analyze_pdf_sections({"subsections": parsed_data})
        
        # Extract evaluation components from matching sections
        components_results = await parse_evaluation_components(analysis_results)
        
        return components_results
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Component extraction failed: {str(e)}"}
        )

