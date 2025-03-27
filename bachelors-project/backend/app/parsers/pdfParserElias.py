import fitz  # PyMuPDF for text and images
import pdfplumber  # For table extraction
import re

def extract_everything(pdf_path):
    """Extracts EVERYTHING from the PDF: all text, sections, subsections, numbers, tables, and structure."""
    doc = fitz.open(pdf_path)
    extracted_data = {"content": []}  # Store everything in a structured order
    current_title = None  # Track the current section or subsection
    current_content = []  # Store content under the current section

    # Define a threshold for font size (adjust if necessary)
    font_threshold = 12

    # Compile a regex pattern that captures headings like:
    # "1 Title", "1.5 Subtitle", "1.5.1 Another Subtitle", etc.
    heading_pattern = re.compile(r'^(\d+(?:\.\d+)*)(\s+.*)$')

    # Iterate over pages
    for page_num, page in enumerate(doc, 1):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    # Combine text from all spans in the line
                    line_text = " ".join(span["text"].strip() for span in line["spans"])
                    # Skip very short lines (could be headers, footers, or page numbers)
                    if len(line_text) < 5:
                        continue

                    # Determine if any span is bold and get the maximum font size in this line
                    is_bold = any("Bold" in span["font"] for span in line["spans"])
                    max_font_size = max(span["size"] for span in line["spans"])

                    # If the line matches our heading pattern and meets style criteria, treat it as a new section
                    if heading_pattern.match(line_text) and is_bold and max_font_size >= font_threshold:
                        # Save the previous section if it exists
                        if current_title:
                            extracted_data["content"].append({
                                "section": current_title,
                                "text": "\n".join(current_content).strip()
                            })
                            current_content = []
                        current_title = line_text
                    elif current_title:
                        # Otherwise, if we're inside a section, add this line as content
                        current_content.append(line_text)

    # Save any remaining section before finishing
    if current_title:
        extracted_data["content"].append({
            "section": current_title,
            "text": "\n".join(current_content).strip()
        })

    

    return extracted_data


if __name__ == "__main__":
    pdf_path = "Kravspecifikation.pdf"
    extracted_data = extract_sections_and_subsections(pdf_path)

    print("\n FULL PDF Extraction (Text + Tables) in Order:")
    for item in extracted_data["content"]:
        print(f"\n Section: {item['section']}")
        print(f"Content: {item['text']}")
        print("\n---\n")

