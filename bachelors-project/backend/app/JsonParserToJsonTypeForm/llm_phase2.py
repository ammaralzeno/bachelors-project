#!/usr/bin/env python
import asyncio
import json
import re
from typing import Dict, Any
from google import genai
from google.genai import types

# Updated extraction prompt with the desired criteria.
EXTRACTION_PROMPT = """
Språk: Svenska.
Du är en expert på upphandlingsdokument och utvärderingsmodeller för offentliga upphandlingar.
Utifrån följande text, extrahera alla relevanta utvärderingsfrågor eller kriterier, 
samt de tillhörande svarsalternativen, graderingsskalor och eventuella poängsättningar.
Returnera resultatet i JSON-format med följande struktur:
{
  "questions": [ "Fråga 1", "Fråga 2", ... ],
  "scale": [ ... ],            
  "scaleLabels": [ ... ]       
}
Om någon del saknas i texten, returnera en tom lista för den nyckeln. Om det är så att olika frågor har olika alternativ (scale) och scaleLabels då separera frågorna så alla likadana är i samma array och om inte samma som föregående ny array och ny rad. 
Text:
"""

async def extract_section(section_title: str, section_content: str) -> Dict[str, Any]:
    """
    Processes a single section using the LLM to extract evaluation criteria.
    
    Args:
        section_title: The title of the section.
        section_content: The text content of the section.
        
    Returns:
        A dictionary containing the extracted evaluation questions, scale and scaleLabels,
        or error information if extraction fails.
    """
    # Initialize the LLM client. Adjust project and location as needed.
    client = genai.Client(
        vertexai=True,
        project="glass-tide-452711-q2",
        location="europe-central2",
    )
    model = "gemini-2.0-flash-001"
    
    system_prompt = "Språk: Svenska. Du är en expert på upphandlingsdokument."
    user_message = EXTRACTION_PROMPT + f"\nTitel: {section_title}\n\n{section_content}"
    
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
    
    try:
        # Run the LLM call in a separate thread so it doesn't block the asyncio loop.
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        response_text = response.text
        
        # Attempt to extract JSON from the LLM response.
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                extracted = json.loads(json_str)
                # Ensure the expected keys exist; if not, default to empty lists.
                extracted.setdefault("questions", [])
                extracted.setdefault("scale", [])
                extracted.setdefault("scaleLabels", [])
                return extracted
            except json.JSONDecodeError as e:
                return {"error": f"JSON parsing error: {str(e)}", "raw": response_text}
        else:
            return {"error": "Ingen JSON hittades i svaret.", "raw": response_text}
    except Exception as e:
        return {"error": str(e)}
