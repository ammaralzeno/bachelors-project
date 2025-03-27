from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
import os
import traceback

# Configuration for Document AI
PROJECT_ID = "glass-tide-452711-q2"
LOCATION = "eu"
PROCESSOR_ID = "139c61c15adcc30e"

def initialize_document_ai_client():
    """Initialize and return a Document AI client for the EU region"""
    options = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
    return documentai.DocumentProcessorServiceClient(client_options=options)

def process_document(file_path):
    """
    Process a document using Google Document AI OCR and extract hierarchical sections
    
    Args:
        file_path: Path to the PDF file to process
        
    Returns:
        dict: Structured data extracted from the document with hierarchical sections
    """
    try:
        # Initialize Document AI client
        client = initialize_document_ai_client()
        
        # The full resource name of the processor
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

        # Read the file
        with open(file_path, "rb") as doc_file:
            document_content = doc_file.read()

        # Configure the process request
        raw_document = documentai.RawDocument(
            content=document_content,
            mime_type="application/pdf"
        )
        
        # Create the request
        request = documentai.ProcessRequest(
            name=name,
            raw_document=raw_document
        )

        # Process the document
        result = client.process_document(request=request)
        document = result.document

        # Extract document metadata
        metadata = {
            "mime_type": document.mime_type,
            "text_length": len(document.text),
            "page_count": len(document.pages)
        }

        # Extract all paragraphs in order
        all_paragraphs = []
        for page in document.pages:
            for paragraph in page.paragraphs:
                para_text = get_text(paragraph.layout.text_anchor, document.text).strip()
                if para_text:  # Skip empty paragraphs
                    bounding_box = None
                    if hasattr(paragraph.layout, 'bounding_poly') and paragraph.layout.bounding_poly:
                        bounding_box = {
                            "vertices": [
                                {"x": vertex.x, "y": vertex.y} 
                                for vertex in paragraph.layout.bounding_poly.vertices
                            ]
                        }
                    
                    all_paragraphs.append({
                        "text": para_text,
                        "page": page.page_number,
                        "confidence": paragraph.layout.confidence,
                        "bounding_box": bounding_box
                    })

        # Extract hierarchical sections
        hierarchical_sections = extract_hierarchical_sections(all_paragraphs)

        # Final structured data
        structured_data = {
            "metadata": metadata,
            "sections": hierarchical_sections
        }

        return structured_data

    except Exception as e:
        error_info = {
            "error": str(e), 
            "traceback": traceback.format_exc()
        }
        return error_info

def get_text(text_anchor, text):
    """Extract text from a text anchor."""
    if not text_anchor or not text_anchor.text_segments:
        return ""
    result = ""
    for segment in text_anchor.text_segments:
        start_index = segment.start_index
        end_index = segment.end_index
        result += text[start_index:end_index]
    return result

def extract_hierarchical_sections(paragraphs):
    """
    Extract hierarchical sections from paragraphs based on section numbering patterns
    Focuses only on significant section titles and ignores small numbered elements
    
    Args:
        paragraphs: List of paragraph objects with text content
        
    Returns:
        list: Hierarchical structure of sections and subsections
    """
    import re
    
    # Common section numbering patterns
    section_patterns = [
        # 1. Section title
        r'^\s*(\d+)\.?\s+(.+)$',
        # 1.1 Subsection title
        r'^\s*(\d+\.\d+)\.?\s+(.+)$',
        # 1.1.1 Sub-subsection title
        r'^\s*(\d+\.\d+\.\d+)\.?\s+(.+)$',
        # I. Roman numeral section
        r'^\s*(I{1,3}|IV|V|VI{1,3}|IX|X|XI{1,3}|XIV|XV|XVI{1,3}|XIX|XX)\.?\s+(.+)$',
        # A. Lettered section
        r'^\s*([A-Z])\.?\s+(.+)$',
        # (a) Parenthesis section
        r'^\s*\(([a-z])\)\s+(.+)$',
        # Article X.
        r'^\s*Article\s+(\d+|[IVXLCDM]+)\.?\s*(.+)?$',
        # Section X.
        r'^\s*Section\s+(\d+|[IVXLCDM]+)\.?\s*(.+)?$'
    ]
    
    # Initialize the sections hierarchy
    sections = []
    current_sections = {
        "level_1": None,
        "level_2": None,
        "level_3": None
    }
    current_section_content = []
    
    for i, paragraph in enumerate(paragraphs):
        text = paragraph["text"]
        
        # Try to match section patterns
        is_section_header = False
        section_level = 0
        section_number = ""
        section_title = ""
        
        for pattern_index, pattern in enumerate(section_patterns):
            match = re.match(pattern, text)
            if match:
                section_number = match.group(1)
                section_title = match.group(2) if len(match.groups()) > 1 else ""
                
                # Determine section level based on the pattern
                if pattern_index == 0:  # 1. Section title
                    section_level = 1
                elif pattern_index == 1:  # 1.1 Subsection title
                    section_level = 2
                elif pattern_index == 2:  # 1.1.1 Sub-subsection title
                    section_level = 3
                elif pattern_index in [3, 4, 6, 7]:  # Roman numerals, Letters, Article, Section
                    section_level = 1
                elif pattern_index == 5:  # (a) Parenthesis
                    section_level = 2
                
                # NEW: Filter for significant section headers
                # Check if section title has minimum length or contains important words
                title_text = section_title.strip()
                
                # 1. Check title length (ignore very short titles that are likely not real sections)
                min_title_length = 3  # Minimum number of words for a valid section title
                word_count = len(title_text.split())
                
                # 2. Check for important keywords often found in true section titles
                important_keywords = ['introduction', 'summary', 'conclusion', 'background', 'method', 
                                     'procedure', 'result', 'discussion', 'reference', 'appendix',
                                     'scope', 'purpose', 'objective', 'requirement', 'definition',
                                     'information', 'overview', 'specification', 'description']
                
                contains_keyword = any(keyword in title_text.lower() for keyword in important_keywords)
                
                # Set as section header if it passes our criteria
                is_section_header = (word_count >= min_title_length) or contains_keyword
                
                break
        
        # If this is a section header, save the previous section and start a new one
        if is_section_header:
            # Save the current section content if any
            if current_sections["level_1"] is not None:
                if section_level == 1:
                    # Closing a level 1 section
                    if current_section_content:
                        sections[-1]["content"] = "\n".join(current_section_content)
                    current_section_content = []
                elif section_level == 2 and current_sections["level_2"] is not None:
                    # Closing a level 2 section
                    if current_section_content and sections[-1]["subsections"]:
                        sections[-1]["subsections"][-1]["content"] = "\n".join(current_section_content)
                    current_section_content = []
                elif section_level == 3 and current_sections["level_3"] is not None:
                    # Closing a level 3 section
                    if current_section_content and sections[-1]["subsections"] and sections[-1]["subsections"][-1].get("subsections"):
                        sections[-1]["subsections"][-1]["subsections"][-1]["content"] = "\n".join(current_section_content)
                    current_section_content = []
            
            # Create a new section
            if section_level == 1:
                # Create a new top-level section
                new_section = {
                    "number": section_number,
                    "title": section_title.strip(),
                    "subsections": [],
                    "content": ""
                }
                sections.append(new_section)
                current_sections["level_1"] = new_section
                current_sections["level_2"] = None
                current_sections["level_3"] = None
            elif section_level == 2 and current_sections["level_1"] is not None:
                # Create a new subsection
                new_subsection = {
                    "number": section_number,
                    "title": section_title.strip(),
                    "subsections": [],
                    "content": ""
                }
                current_sections["level_1"]["subsections"].append(new_subsection)
                current_sections["level_2"] = new_subsection
                current_sections["level_3"] = None
            elif section_level == 3 and current_sections["level_2"] is not None:
                # Create a new sub-subsection
                new_subsubsection = {
                    "number": section_number,
                    "title": section_title.strip(),
                    "content": ""
                }
                current_sections["level_2"]["subsections"].append(new_subsubsection)
                current_sections["level_3"] = new_subsubsection
        else:
            # This is content for the current section
            current_section_content.append(text)
    
    # Add the final section's content
    if current_sections["level_3"] is not None and current_section_content:
        # Content belongs to level 3
        current_sections["level_3"]["content"] = "\n".join(current_section_content)
    elif current_sections["level_2"] is not None and current_section_content:
        # Content belongs to level 2
        current_sections["level_2"]["content"] = "\n".join(current_section_content)
    elif current_sections["level_1"] is not None and current_section_content:
        # Content belongs to level 1
        current_sections["level_1"]["content"] = "\n".join(current_section_content)
    
    # If no sections were found, create a single unnamed section with all content
    if not sections and paragraphs:
        all_text = "\n".join([p["text"] for p in paragraphs])
        sections = [{
            "title": "Unnamed Section",
            "content": all_text,
            "subsections": []
        }]
    
    return sections