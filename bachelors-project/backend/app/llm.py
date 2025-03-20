from google import genai
from google.genai import types
import base64
import asyncio
from typing import List, Dict, Any

# Define the criteria here as a constant
ANALYSIS_CRITERIA = """
Evaluera om texten innehåller något av följande:

- pris
- mervärde
- mervärdeskriterier
- tilldelningskriterie(r)
- utvärdering
- ersättning
- utvärderingsmodell
- Att lämna anbud
- utvärderingsmetod
- utvärdering
- utvärderingsgrund
- prövning av anbud
- mervärdeskrav
- utvärderingskriterie(r)
- utvärdering av anbud

Dokumentet är en utvärderingsrapport för en upphandling.


Svara med YES om det finns något i texten som uppfyller kriterierna, och NO om det inte finns.
"""

async def process_section(title: str, content: str) -> Dict[str, Any]:
    """
    Process a single PDF section with the LLM and check if it meets criteria.
    
    Args:
        title: The title of the section
        content: The text content of the section
        
    Returns:
        Dictionary with section title, content and whether it meets criteria
    """
    client = genai.Client(
        vertexai=True,
        project="glass-tide-452711-q2",
        location="europe-central2",
    )

    model = "gemini-2.0-flash-001"
    
    system_prompt = "Språk: Svenska. Du är en expert dokumentanalysator. Utvärdera om följande dokumentavsnitt uppfyller något av kriterierna."
    user_message = f"Kriterier: {ANALYSIS_CRITERIA}\n\nAvsnitt: {title}\n\nInnehåll: {content}"
    
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": system_prompt},
                {"text": user_message}
            ]
        }
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=1024,
        response_mime_type="application/json",
    )

    response_text = ""
    try:
        # For async operation, we'll use the non-streaming version
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        response_text = response.text
        
        # Simple check if criteria is met (you can make this more sophisticated)
        meets_criteria = "yes" in response_text.lower() or "true" in response_text.lower()
        
        return {
            "title": title,
            "content": content,
            "meets_criteria": meets_criteria,
            "analysis": response_text
        }
    except Exception as e:
        return {
            "title": title,
            "content": content,
            "meets_criteria": False,
            "analysis": f"Error: {str(e)}"
        }

async def process_sections(subsections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Process multiple PDF sections in parallel and return those that meet criteria.
    
    Args:
        subsections: Dictionary where keys are section titles and values are section content
        
    Returns:
        List of sections that meet the criteria with their analysis
    """
    tasks = [process_section(title, content) for title, content in subsections.items()]
    results = await asyncio.gather(*tasks)
    
    # Filter for sections that meet criteria
    matching_sections = [result for result in results if result["meets_criteria"]]
    
    return matching_sections

async def process_pdf_page(page_num: int, page_content: str) -> Dict[str, Any]:
    """
    Process a single PDF page with the LLM and extract sections that meet criteria.
    
    Args:
        page_num: The page number
        page_content: The text content of the page
        
    Returns:
        Dictionary with page info, extracted sections, and whether it meets criteria
    """
    client = genai.Client(
        vertexai=True,
        project="glass-tide-452711-q2",
        location="europe-central2",
    )

    model = "gemini-2.0-flash-001"
    
    system_prompt = """Språk: Svenska. Du är en expert dokumentanalysator. 
    1. Utvärdera om följande dokumentsida uppfyller något av kriterierna.
    2. Identifiera alla numrerade sektioner (t.ex. "1 Titel", "1.1 Undertitel") på sidan.
    3. För varje sektion, extrahera innehållet som hör till den sektionen.
    4. Returnera resultatet i JSON-format med följande struktur:
    {
      "meets_criteria": "YES/NO",
      "sections": {
        "1 Titel": "Innehåll för sektion 1...",
        "1.1 Undertitel": "Innehåll för sektion 1.1..."
      }
    }
    """
    
    user_message = f"Kriterier: {ANALYSIS_CRITERIA}\n\nSida: {page_num}\n\nInnehåll: {page_content}"
    
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": system_prompt},
                {"text": user_message}
            ]
        }
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=2048,
        response_mime_type="application/json",
    )

    try:
        # For async operation, we'll use the non-streaming version
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        
        response_text = response.text
        
        # Parse the JSON response
        import json
        import re
        
        # Try to find JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                parsed_response = json.loads(json_str)
                
                # Extract meets_criteria and sections
                meets_criteria = False
                if isinstance(parsed_response, dict):
                    if "meets_criteria" in parsed_response:
                        meets_criteria = parsed_response["meets_criteria"].upper() == "YES"
                    sections = parsed_response.get("sections", {})
                else:
                    sections = {}
                    
                return {
                    "page_num": page_num,
                    "content": page_content,
                    "meets_criteria": meets_criteria,
                    "sections": sections,
                    "analysis": response_text
                }
            except json.JSONDecodeError:
                # Fallback to regex if JSON parsing fails
                pass
        
        # Fallback: use regex to find section patterns
        meets_criteria = "yes" in response_text.lower()
        sections = {}
        
        # Extract sections using regex
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
            
            sections[full_title] = section_content
        
        return {
            "page_num": page_num,
            "content": page_content,
            "meets_criteria": meets_criteria,
            "sections": sections,
            "analysis": response_text
        }
    except Exception as e:
        return {
            "page_num": page_num,
            "content": page_content,
            "meets_criteria": False,
            "sections": {},
            "analysis": f"Error: {str(e)}"
        }
