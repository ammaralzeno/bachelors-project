import os
from pdf2docx import Converter
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def convert_pdf_to_docx(pdf_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert a PDF file to DOCX format.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_path (Optional[str]): Path for the output DOCX file. If None, 
                                    will use the same name as the PDF but with .docx extension
    
    Returns:
        str: Path to the converted DOCX file
    
    Raises:
        FileNotFoundError: If the input PDF file doesn't exist
        Exception: For any other errors during conversion
    """
    try:
        # Check if input file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Generate output path if not provided
        if output_path is None:
            output_path = os.path.splitext(pdf_path)[0] + '.docx'
        
        # Create directory for output file if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Convert PDF to DOCX
        logger.info(f"Converting PDF to DOCX: {pdf_path} -> {output_path}")
        cv = Converter(pdf_path)
        cv.convert(output_path)
        cv.close()
        
        logger.info(f"Conversion completed successfully")
        return output_path
    
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error converting PDF to DOCX: {str(e)}")
        raise Exception(f"Failed to convert PDF to DOCX: {str(e)}")

if __name__ == "__main__":
    # Example usage
    sample_pdf = "path/to/sample.pdf"
    try:
        output_file = convert_pdf_to_docx(sample_pdf)
        print(f"Converted file saved to: {output_file}")
    except Exception as e:
        print(f"Conversion failed: {str(e)}")
