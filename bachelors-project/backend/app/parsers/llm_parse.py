import fitz  # PyMuPDF
import asyncio
import json
import re
from typing import Dict, List, Any
import os
from app.llm import process_pdf_page

async def extract_text_from_page(page) -> str:
    """
    Extract text content from a single PDF page.
    
    Args:
        page: A PyMuPDF page object
        
    Returns:
        String containing all text from the page
    """
    return page.get_text()

async def process_pdf_with_llm(pdf_path: str) -> Dict[str, Any]:
    """
    Process a PDF document by splitting it into pages and analyzing each page with LLM.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing sections that match the criteria
    """
    # Open the PDF
    doc = fitz.open(pdf_path)
    
    # Extract text from each page in parallel
    tasks = [extract_text_from_page(page) for page in doc]
    page_texts = await asyncio.gather(*tasks)
    
    # Process each page with LLM in parallel
    page_tasks = []
    for page_num, page_text in enumerate(page_texts):
        # Process this page with the LLM
        page_tasks.append(process_pdf_page(page_num + 1, page_text))
    
    # Wait for all LLM processing to complete
    page_results = await asyncio.gather(*page_tasks)
    
    # Filter for pages that meet criteria
    matching_pages = [result for result in page_results if result["meets_criteria"]]
    
    # Organize results
    return {
        "matching_pages": matching_pages,
        "total_pages": len(page_texts),
        "all_pages": page_results  # Include all pages for debugging
    }

async def extract_sections_with_llm(pdf_path: str) -> Dict[str, Any]:
    """
    Higher-level function to extract sections from a PDF using LLM analysis.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing structured content from the PDF
    """
    # Process the PDF with LLM
    results = await process_pdf_with_llm(pdf_path)
    
    # Combine all sections from matching pages
    all_sections = {}
    
    # First, try to extract sections from LLM output
    for page_result in results["matching_pages"]:
        page_sections = page_result.get("sections", {})
        
        # Merge sections from this page with existing sections
        for section_title, section_content in page_sections.items():
            # Skip if section_title is not a string
            if not isinstance(section_title, str):
                continue
                
            # Skip if section_content is not a string
            if not isinstance(section_content, str):
                continue
                
            if section_title in all_sections:
                all_sections[section_title] += f"\n{section_content}"
            else:
                all_sections[section_title] = section_content
    
    # If no sections were found, fall back to manual extraction
    if not all_sections:
        # Extract sections manually from the content
        for page_result in results["matching_pages"]:
            page_content = page_result["content"]
            
            # Look for patterns like "1 Title" or "1.1 Subtitle"
            section_pattern = r'(\d+(\.\d+)?)\s+([^\n]+)'
            section_matches = re.finditer(section_pattern, page_content)
            
            for match in section_matches:
                section_num = match.group(1)
                section_title = match.group(3)
                full_title = f"{section_num} {section_title}"
                
                # Extract content following this section title until the next section title
                start_pos = match.end()
                next_match = re.search(section_pattern, page_content[start_pos:])
                
                if next_match:
                    end_pos = start_pos + next_match.start()
                    section_content = page_content[start_pos:end_pos].strip()
                else:
                    section_content = page_content[start_pos:].strip()
                
                # Add or append to existing section
                if full_title in all_sections:
                    all_sections[full_title] += f"\n{section_content}"
                else:
                    all_sections[full_title] = section_content
    
    return {
        "sections": all_sections,
        "analysis_summary": {
            "total_pages": results["total_pages"],
            "matching_pages": len(results["matching_pages"])
        }
    }

if __name__ == "__main__":
    # Example usage
    pdf_path = "backend/uploads/Kravspecifikation.pdf"
    
    async def test():
        result = await extract_sections_with_llm(pdf_path)
        
        print(f"\nAnalysis Summary:")
        print(f"Total Pages: {result['analysis_summary']['total_pages']}")
        print(f"Matching Pages: {result['analysis_summary']['matching_pages']}")
        
        print("\nExtracted Sections:")
        for title, content in result["sections"].items():
            print(f"\n{title}")
            print("-" * len(title))
            print(f"{content[:200]}..." if len(content) > 200 else content)
    
    # Run the async test function
    asyncio.run(test()) 