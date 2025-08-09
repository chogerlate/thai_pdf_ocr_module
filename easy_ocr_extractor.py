#!/usr/bin/env python3
"""
PDF to Text OCR Extractor
Converts PDF files in a directory to text files using EasyOCR.
Supports Thai and English text recognition.

Usage: python pdf_ocr_extractor.py <input_pdf_dir> <output_txt_dir>
"""

import os
import sys
import argparse
from pdf2image import convert_from_path
import easyocr
import numpy as np


def pdfs_to_easyocr_text(pdf_dir, output_txt_dir):
    """
    Convert PDFs in directory to text files using OCR and save in output directory.
    
    Args:
        pdf_dir (str): Directory containing PDF files
        output_txt_dir (str): Directory to save extracted text files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_txt_dir, exist_ok=True)
    
    # Initialize EasyOCR reader for Thai and English
    print("Initializing EasyOCR reader...")
    reader = easyocr.Reader(['th', 'en'])
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print(f"Processing: {pdf_file}")
        
        try:
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=300)
            print(f"  Converted to {len(pages)} page(s)")
        except Exception as e:
            print(f"  Failed to convert {pdf_file}: {e}")
            continue
        
        all_text = []
        
        # Process each page
        for i, page in enumerate(pages):
            print(f"  Processing page {i+1}/{len(pages)}")
            
            # Convert PIL image to numpy array
            img_np = np.array(page)
            
            # Extract text using EasyOCR
            text = reader.readtext(img_np, detail=0, paragraph=True)
            
            # Add page separator and text
            all_text.append(f"--- Page {i+1} ---")
            all_text.extend(text)
            all_text.append("\n")
        
        # Write output text file with same base name
        base_name = os.path.splitext(pdf_file)[0]
        txt_file_path = os.path.join(output_txt_dir, f"{base_name}.txt")
        
        try:
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(all_text))
            print(f"  Saved OCR text to: {txt_file_path}")
        except Exception as e:
            print(f"  Failed to save {txt_file_path}: {e}")
    
    print("Processing complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files using OCR (Thai/English support)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_ocr_extractor.py ./pdfs ./output_texts
  python pdf_ocr_extractor.py /path/to/pdfs /path/to/output
        """
    )
    
    parser.add_argument(
        'input_dir',
        help='Directory containing PDF files to process'
    )
    
    parser.add_argument(
        'output_dir', 
        help='Directory to save extracted text files'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='DPI for PDF to image conversion (default: 300)'
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    # Convert paths to absolute paths
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    
    print(f"Input PDF directory: {input_dir}")
    print(f"Output text directory: {output_dir}")
    print()
    
    # Process PDFs
    pdfs_to_easyocr_text(input_dir, output_dir)


if __name__ == "__main__":
    main()