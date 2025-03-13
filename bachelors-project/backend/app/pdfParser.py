import fitz  # PyMuPDF
import re

def extract_titles_from_pdf(pdf_path):
    """Extracts section titles from a PDF document based on font size and numbering."""
    doc = fitz.open(pdf_path)
    titles = []
    
    for page in doc:
        blocks = page.get_text("dict")["blocks"]  
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        font_size = span["size"]
                        
                       
                        if re.match(r'^[0-9]+(\.[0-9]+)*\s+.*', text):
                            titles.append(text)
    
    return titles


if __name__ == "__main__":
    pdf_path = "Kravspecifikation.pdf"
    titles = extract_titles_from_pdf(pdf_path)
    for title in titles:
        print(title)
