from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnno
import pdfplumber  # For extracting tables
import re

def extract_everything(pdf_path):
    """Extracts all structured content from the PDF: sections, subsections, text, and tables while preserving order."""
    extracted_data = {"content": [], "tables": []}  # Store all extracted content
    current_title = None  # Track the current section/subsection
    current_content = []  # Store content for the current section

    # Extract text-based sections & content while preserving order
    for page_num, page_layout in enumerate(extract_pages(pdf_path), start=1):
        for element in page_layout:
            if isinstance(element, LTTextContainer):  # Extract text elements
                line_text = "".join([char.get_text() for char in element if isinstance(char, (LTChar, LTAnno))]).strip()

                if not line_text or len(line_text) < 5:  # Ignore empty/short lines
                    continue

                # Detect main sections (e.g., "1 Title")
                if re.match(r'^\d+\s+.*', line_text):  
                    if current_title:
                        extracted_data["content"].append({"section": current_title, "text": "\n".join(current_content).strip()})
                        current_content = []  
                    current_title = line_text  

                # Detect sub-sections (e.g., "1.1 Subtitle")
                elif re.match(r'^\d+\.\d+\s+.*', line_text):  
                    if current_title:
                        extracted_data["content"].append({"section": current_title, "text": "\n".join(current_content).strip()})
                        current_content = []
                    current_title = line_text  

                # Capture regular text between sections
                elif current_title:
                    current_content.append(line_text)

    # Store last section before exiting
    if current_title:
        extracted_data["content"].append({"section": current_title, "text": "\n".join(current_content).strip()})

    # Extract tables while preserving order
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                if table:  # Only store non-empty tables
                    structured_table = [[str(cell).strip() if cell else "" for cell in row] for row in table]
                    extracted_data["tables"].append({"page": page_num, "table": structured_table})

    return extracted_data

# ----------------- RUN THE SCRIPT -----------------
if __name__ == "__main__":
    pdf_path = "Kravspecifikation.pdf"  # Update with actual file path
    extracted_data = extract_everything(pdf_path)

    print("\n✅ FULL PDF Extraction (Text + Tables) in Order:")

    for item in extracted_data["content"]:
        print(f"\n📌 Section: {item['section']}")
        print(f"📄 Content: {item['text']}")
        print("\n---\n")

    print("\n✅ Extracted Tables:")
    for table_data in extracted_data["tables"]:
        print(f"\n📊 Table from Page {table_data['page']}:")
        for row in table_data["table"]:
            print(row)
        print("\n---\n")
