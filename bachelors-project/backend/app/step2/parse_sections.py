from google import generativeai as genai
import asyncio
import os
from typing import List, Dict, Any
from dotenv import load_dotenv


load_dotenv()

COMPONENT_CLASSIFICATION_PROMPT = """
Analysera texten och identifiera vilka komponenter som bäst passar för att representera informationen i utvärderingsmodellen.

Du ska svara med en eller flera komponenter från följande alternativ:
1. "inputbox" - För direkta värden som anbudspris
2. "slider" - För poängbaserade intervaller som referenspoäng
3. "radio" - För kategoriska val med olika utvärderingseffekter
4. "yesno" - För ja/nej-frågor med olika effekter

För varje komponent du identifierar, ange följande i JSON-format:
- id: ett unikt id (använd ett enkelt beskrivande namn utan mellanslag)
- content: rubriken/frågan för komponenten
- type: komponenttyp (inputbox, slider, radio, yesno)
- alternatives: möjliga värden (tom lista för inputbox)
- evaluation: hur svaret påverkar utvärderingen
  - operation: "base" (utgångsvärde), "adjust" (justera med fast värde), "percent" (procentuell justering)
  - valueType: "direct", "range", eller "map"
  - ranges/mapping: definiera intervall eller mappningar om tillämpligt

Exempel:
För anbudspris:
{
  "id": "anbudspris",
  "content": "Anbudspris",
  "type": "inputbox",
  "alternatives": [""],
  "evaluation": {
    "operation": "base",
    "valueType": "direct"
  }
}

För referenspoäng:
{
  "id": "referenspoang",
  "content": "Referenspoäng",
  "type": "slider",
  "alternatives": ["55 - 64", "35 - 54", "15 - 34", "0 - 14"],
  "evaluation": {
    "operation": "adjust",
    "valueType": "range",
    "ranges": [
      { "min": 55, "max": 64, "value": -600000 },
      { "min": 35, "max": 54, "value": -300000 },
      { "min": 15, "max": 34, "value": 300000 },
      { "min": 0, "max": 14, "value": 600000 }
    ]
  }
}

För kvalitativa utvärderingar:
{
  "id": "kvalitet",
  "content": "Kvalitetsnivå",
  "type": "radio",
  "alternatives": ["Låg", "Medel", "Hög"],
  "evaluation": {
    "operation": "percent",
    "valueType": "map",
    "mapping": {
      "Låg": 0,
      "Medel": -0.10,
      "Hög": -0.20
    }
  }
}

För ja/nej-frågor:
{
  "id": "harCertifiering",
  "content": "Har certifiering?",
  "type": "yesno",
  "alternatives": ["Ja", "Nej"],
  "evaluation": {
    "operation": "adjust",
    "valueType": "map",
    "mapping": {
      "Ja": -50000,
      "Nej": 0
    }
  }
}

Svara med exakt JSON-format för alla komponenter du hittar i texten. Om flera komponenter identifieras, lägg dem i en array. Utelämna allt annat i ditt svar.
"""

async def process_section_for_components(section: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single matching section with the LLM to identify evaluation components.
    
    Args:
        section: Dictionary containing 'section' (title) and 'content' (text)
        
    Returns:
        Dictionary with the components identified from the section
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return {
                "section": section["section"],
                "error": "GOOGLE_API_KEY environment variable not set"
            }
            
        # Configure the API with the key
        genai.configure(api_key=api_key)
        
        # Set up the model
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_output_tokens": 2048,
        }
        
        # Create the model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-001", 
            generation_config=generation_config
        )
        
        system_prompt = "Du är en expert på att analysera utvärderingsmodeller i offentliga upphandlingar och omvandla dem till interaktiva komponenter."
        user_message = f"Här är texten från ett avsnitt i en utvärderingsmodell:\n\nAvsnitt: {section['section']}\n\nInnehåll: {section['content']}\n\n{COMPONENT_CLASSIFICATION_PROMPT}"
        
        # Send the message directly without starting a chat
        response = await asyncio.to_thread(
            model.generate_content,
            f"{system_prompt}\n\n{user_message}"
        )
        
        response_text = response.text
        
        # Clean up response - try to extract just the JSON part
        import json
        import re
        
        # Look for JSON pattern in the response
        json_match = re.search(r'(\[\s*{.*}\s*\]|\{\s*"id".*\})', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Parse JSON to validate format
            try:
                components = json.loads(json_str)
                # Ensure components is a list
                if not isinstance(components, list):
                    components = [components]
                return {
                    "section": section["section"],
                    "components": components
                }
            except json.JSONDecodeError:
                return {
                    "section": section["section"],
                    "error": "Failed to parse LLM response as JSON",
                    "raw_response": response_text
                }
        else:
            return {
                "section": section["section"],
                "error": "No valid JSON found in LLM response",
                "raw_response": response_text
            }
            
    except Exception as e:
        return {
            "section": section["section"],
            "error": f"Error: {str(e)}"
        }

async def parse_matching_sections(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process all matching sections together in a single LLM call to extract evaluation components.
    
    Args:
        analysis_results: The output from analyze_pdf_sections
        
    Returns:
        Dictionary with evaluation components for all matching sections
    """
    matching_sections = analysis_results.get("matching_sections", [])
    
    if not matching_sections:
        return {
            "success": False,
            "message": "No matching sections found in the analysis results",
            "questions": []
        }
    
    try:
        # Get API key from environment
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "message": "GOOGLE_API_KEY environment variable not set",
                "questions": []
            }
            
        # Configure the API with the key
        genai.configure(api_key=api_key)
        
        # Set up the model
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_output_tokens": 2048,
        }
        
        # Create the model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-001", 
            generation_config=generation_config
        )
        
        # Combine all section content into a single text
        combined_sections = ""
        for section in matching_sections:
            combined_sections += f"\n\n===== SECTION: {section['section']} =====\n{section['content']}"
        
        system_prompt = "Du är en expert på att analysera utvärderingsmodeller i offentliga upphandlingar och omvandla dem till interaktiva komponenter."
        user_message = f"Här är texten från alla relevanta avsnitt i en utvärderingsmodell:\n{combined_sections}\n\n{COMPONENT_CLASSIFICATION_PROMPT}\n\nViktigt: Identifiera varje unikt komponent ENDAST EN GÅNG, även om samma information förekommer i flera avsnitt."
        
        # Send the message directly without starting a chat
        response = await asyncio.to_thread(
            model.generate_content,
            f"{system_prompt}\n\n{user_message}"
        )
        
        response_text = response.text
        
        # Clean up response - try to extract just the JSON part
        import json
        import re
        
        # Look for JSON pattern in the response
        json_match = re.search(r'(\[\s*{.*}\s*\]|\{\s*"id".*\})', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Parse JSON to validate format
            try:
                components = json.loads(json_str)
                # Ensure components is a list
                if not isinstance(components, list):
                    components = [components]
                
                # Generate a simple calculationOrder (order of questions based on their type)
                calculation_order = []
                # Always put base components first
                for component in components:
                    if component.get("evaluation", {}).get("operation") == "base":
                        calculation_order.append(component["id"])
                # Then add the rest
                for component in components:
                    if component["id"] not in calculation_order:
                        calculation_order.append(component["id"])
                
                return {
                    "success": True,
                    "questions": components,
                    "calculationOrder": calculation_order
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "message": "Failed to parse LLM response as JSON",
                    "raw_response": response_text,
                    "questions": []
                }
        else:
            return {
                "success": False,
                "message": "No valid JSON found in LLM response",
                "raw_response": response_text,
                "questions": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing sections: {str(e)}",
            "questions": []
        }

async def parse_evaluation_components(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point to parse evaluation components from matching sections.
    
    Args:
        analysis_results: The output from analyze_pdf_sections
        
    Returns:
        Dictionary with evaluation components
    """
    try:
        return await parse_matching_sections(analysis_results)
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing PDF sections: {str(e)}",
            "questions": []
        }
