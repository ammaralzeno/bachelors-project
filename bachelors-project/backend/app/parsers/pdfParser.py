import fitz  # PyMuPDF for text and images
import pdfplumber  # For table extraction
import re

def extract_sections_and_subsections(pdf_path):
    """Extracts EVERYTHING from the PDF: all text, sections, subsections, numbers, tables, and structure."""
    doc = fitz.open(pdf_path)
    extracted_data = {"content": []}  # Store everything in a structured order
    current_title = None  # Track the current section or subsection
    current_content = []  # Store content under the current section

    # Extract text-based sections & content in the same order as in the PDF
    for page_num, page in enumerate(doc, 1):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = " ".join(span["text"].strip() for span in line["spans"])

                    # Ignore very short lines (likely headers, footers, or page numbers)
                    if len(line_text) < 5:
                        continue  

                    # Detect and store main sections (e.g., "1 Title")
                    if re.match(r'^\d+\s+.*', line_text):  
                        if current_title:
                            extracted_data["content"].append({"section": current_title, "text": "\n".join(current_content).strip()})
                            current_content = []  
                        current_title = line_text  

                    # Detect and store sub-sections (e.g., "1.1 Subtitle")
                    elif re.match(r'^\d+\.\d+\s+.*', line_text):  
                        if current_title:
                            extracted_data["content"].append({"section": current_title, "text": "\n".join(current_content).strip()})
                            current_content = []
                        current_title = line_text  

                    # Capture general text between sections
                    elif current_title:
                        current_content.append(line_text)

    # Store the last section before exiting
    if current_title:
        extracted_data["content"].append({"section": current_title, "text": "\n".join(current_content).strip()})


    return extracted_data


if __name__ == "__main__":
    pdf_path = "Kravspecifikation.pdf"
    extracted_data = extract_sections_and_subsections(pdf_path)

    print("\n FULL PDF Extraction (Text + Tables) in Order:")
    for item in extracted_data["content"]:
        print(f"\n Section: {item['section']}")
        print(f"Content: {item['text']}")
        print("\n---\n")

    print("\n Extracted Tables:")
    for table_data in extracted_data["tables"]:
        print(f"\n Table from Page {table_data['page']}:")
        for row in table_data["table"]:
            print(row)
        print("\n---\n")
