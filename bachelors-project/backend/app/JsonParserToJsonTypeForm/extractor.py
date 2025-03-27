#!/usr/bin/env python
import asyncio
import json
from typing import Dict, Any
from llm_phase2 import extract_section  # Import the LLM extraction function

async def process_all_sections(input_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes multiple sections concurrently using asyncio.
    
    Args:
        input_json: Dictionary where keys are section titles and values are dictionaries with the key "content".
    
    Returns:
        A dictionary mapping each section title to the extracted evaluation data.
    """
    tasks = []
    section_titles = []

    for section_title, section_data in input_json.items():
        content = ""
        if isinstance(section_data, list) and len(section_data) > 0:
            content = section_data[0].get("content", "")
        elif isinstance(section_data, dict):
            content = section_data.get("content", "")
        tasks.append(extract_section(section_title, content))
        section_titles.append(section_title)

    # Run all LLM tasks in parallel
    results = await asyncio.gather(*tasks)

    # Map results back to section titles
    return {title: result for title, result in zip(section_titles, results)}

def main():
    # Sample input JSON with sections.
    sample_input = {
  "6.2 Utvärdering": [
    {
      "content": "Totalt kommer två (2) referensuppdrag att utvärderas. Uppdragen kan vara pågående eller avslutade men ska ha pågått under minst en tvåårsperiod med minst 25 beställningar per år. Referensuppdragen kommer att användas för att utvärdera anbudsgivarens kvalitet i utförande av efterfrågade produkter och tjänster. Leverantörens genomförande av ingivna referensuppdrag kommer att utvärderas genom att angiven referent bedömer hur väl leverantören har utfört refererat uppdrag genom nedan ställda frågor. Referensuppdragen ska ha utförts den senaste treårsperioden."
    }
  ],
  "6.2.1 Referenstagning": [
    {
      "content": "Kommunen kommer att ställa följande åtta (8) frågor till referensens kontaktperson:\n1. Erbjuder leverantören tillräcklig utbildning, support och underhåll efter installation av nya brandskyddsprodukter?\n2. Har kommunikationen mellan leverantör och beställare varit effektiv och tillfredsställande under hela avtalstiden?\n3. Skulle ni rekommendera denna leverantör till andra inom samma bransch?\n4. Har ni känt er trygga med leverantörens brandskyddslösningar och säkerhetsåtgärder?\n5. Har leverantören levererat enligt avtalade tidsramar?\n6. Har alla förväntade leveranser och prestationer genomförts enligt det fastställda avtalet?\n7. Har faktureringen genomförts korrekt, utan att några dolda kostnader eller tillägg har upptäckts vid granskning/avtalsuppföljning?\n8. Har leverantören varit flexibel och lösningsorienterad när/om det uppstod problem eller frågor?"
    },
    {
      "content": "Frågorna ska besvaras med poängsättning enligt följande:\n4 poäng: Alltid\n3 poäng: Ofta\n2 poäng: Ibland\n1 poäng: Sällan\n0 poäng: Aldrig\nVarje fråga ger max 4 poäng, totalt ger frågorna max 64 poäng (8 frågor * max 4 poäng * 2 referenser)."
    }
  ],
  "6.2.2 Referensrutiner": [
    {
      "content": "Kommunen kommer att kontakta kontaktpersonerna via e-post under utvärderingsfasen. Kontaktpersonen kommer att ha fem (5) arbetsdagar på sig att besvara frågorna. Om kontaktpersonen inte har svarat när en (1) dag återstår kommer en påminnelse att sändas till kontaktpersonen, anbudsgivaren kommer att läggas som kopia i e-posten. Om kontaktpersonen ändå inte inkommer med svar på referensfrågorna i tid kommer poängen på samtliga frågor bli 0."
    },
    {
      "content": "Anbudsgivaren får lämna ny kontaktperson för samma referensuppdrag. Sådan ny kontaktperson måste dock besvara referensfrågorna inom den ovan angivna svarstiden och leva upp till de obligatoriska kraven för referensuppdrag ovan. Anbudsgivaren får inte lämna nytt referensuppdrag annat än om angiven kontaktperson har oförutsedd frånvaro. Kontakt bör därför tas med kontaktpersonen för referensuppdraget innan hen lämnas som kontaktperson. Nytt referensuppdrag måste leva upp till kraven för referensuppdrag och kontaktpersonen måste besvara referensfrågorna inom den ovan angivna svarstiden."
    },
    {
      "content": "Kommunen kan komma att använda en egen referens om anbudsgivaren tidigare utfört likvärdiga uppdrag åt Kommunen. I det fall kommer Kommunens referens att ersätta en av dem lämnade referenserna genom lottning med tre personer närvarande. Om egen referens används, kommer den person som lämnar referens för Kommunen, inte att delta i utvärderingen."
    }
  ],
  "6.2.3 Poängavdrag eller tillägg": [
    {
      "content": "Följande avdrag/tillägg kommer att läggas på priset, utifrån erhållna referenspoäng.\n55 - 64 poäng; avdrag med 600 000\n35 - 54 poäng; avdrag med 300 000\n15 - 34 poäng; tillägg med 300 000\n0 - 14 poäng; tillägg med 600 000"
    },
    {
      "content": "Utvärderingssumma = Anbudspris (Totalsumma i prismatris Brandskydd) +/- erhållet avdrag/tillägg för referenspoängen. Vid lika utvärderingssumma kommer i anbud med högre referenspoäng att ges företräde."
    }
  ],
  "6.2.4 Referensinformation": [
    {
      "content": "Ange dina två referenser i nedan frifält med följande information:\n- Uppdragsgivare\n- Kontaktperson med telefonnummer och e-postadress\n- Kort beskrivning av uppdraget och dess omfattning\n- Tidpunkt för utförandet av uppdraget\nFritext"
    }
  ]
}

    
    async def run_extraction():
        extracted_results = await process_all_sections(sample_input)
        print(json.dumps(extracted_results, indent=2, ensure_ascii=False))
    
    asyncio.run(run_extraction())

if __name__ == "__main__":
    main()
