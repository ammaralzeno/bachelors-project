from google import generativeai as genai
import asyncio
from typing import List, Dict, Any
import os
from dotenv import load_dotenv


load_dotenv()

SECTION_ANALYSIS_CRITERIA = """
Evaluera om texten innehåller något av följande:

- pris
- avdrag
- tillägg
- mervärde
- mervärdeskriterier
- tilldelningskriterie(r)
- utvärdering
- ersättning
- utvärderingsmodell
- utvärderingsmetod
- utvärdering
- mervärdeskrav
- utvärderingskriterie(r)
- utvärdering av anbud

Texten är en del av en utvärderingsrapport för en offentlig upphandling. 
Vi vill få ut information om hur mycket poäng som har tilldelats och vilka avdrag eller tillägg som har gjorts på slutgiltiga priset.
Du ska endast analysera om texten innehåller information om poäng, kriterier, utvärderingsgrunder, prövning av anbud eller något annat som kan hjälpa oss att avgöra hur mycket poäng som har tilldelats och vilka avdrag eller tillägg som har gjorts på slutgiltiga priset.

Svara med YES om det finns något i texten som uppfyller kriterierna, och NO om det inte finns.
"""

async def process_pdf_section(section: Dict[str, str]) -> Dict[str, Any]:
    """
    Process a single PDF section with the LLM and check if it meets criteria.
    
    Args:
        section: Dictionary containing 'section' (title) and 'text' (content)
        
    Returns:
        Dictionary with section info and whether it meets criteria
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return {
                "section": section["section"],
                "content": section["text"],
                "meets_criteria": False,
                "analysis": "Error: GOOGLE_API_KEY environment variable not set. Make sure to add it to your .env file and install python-dotenv."
            }
            
        # Configure the API with the key
        genai.configure(api_key=api_key)
        
        # Set up the model
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_output_tokens": 1024,
        }
        
        # Create the model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-001", 
            generation_config=generation_config
        )
        
        system_prompt = "Språk: Svenska. Du är en expert dokumentanalysator. Utvärdera om följande dokumentavsnitt uppfyller något av kriterierna."
        user_message = f"Kriterier: {SECTION_ANALYSIS_CRITERIA}\n\nAvsnitt: {section['section']}\n\nInnehåll: {section['text']}"
        
        # Send the message directly without starting a chat
        response = await asyncio.to_thread(
            model.generate_content,
            f"{system_prompt}\n\n{user_message}"
        )
        
        response_text = response.text
        
        # Check if criteria is met
        meets_criteria = "yes" in response_text.lower() or "true" in response_text.lower()
        
        return {
            "section": section["section"],
            "content": section["text"],
            "meets_criteria": meets_criteria,
            "analysis": response_text
        }
    except Exception as e:
        return {
            "section": section["section"],
            "content": section["text"],
            "meets_criteria": False,
            "analysis": f"Error: {str(e)}"
        }

async def process_pdf_sections(parsed_pdf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process PDF sections in parallel and extract those that meet criteria.
    
    Args:
        parsed_pdf_data: The output from pdfParser containing sections
        
    Returns:
        Dictionary with all sections and matching sections that meet criteria
    """
    sections = parsed_pdf_data.get("subsections", {}).get("content", [])
    
    if not sections:
        return {
            "status": "error",
            "message": "No sections found in the parsed PDF data",
            "matching_sections": []
        }
    
    # Create tasks for processing each section in parallel
    tasks = [process_pdf_section(section) for section in sections]
    results = await asyncio.gather(*tasks)
    
    # Filter sections that meet criteria
    matching_sections = [result for result in results if result["meets_criteria"]]
    
    return {
        "status": "success",
        "total_sections": len(sections),
        "matching_count": len(matching_sections),
        "all_sections": results,
        "matching_sections": matching_sections
    }

async def analyze_pdf_sections(parsed_pdf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point to analyze PDF sections from parser output.
    
    Args:
        parsed_pdf_data: The output from pdfParser
        
    Returns:
        Analysis results with matching sections
    """
    try:
        return await process_pdf_sections(parsed_pdf_data)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing PDF sections: {str(e)}",
            "matching_sections": []
        }
