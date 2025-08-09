# Thai OCR PDF Extractor

![Our Solution](assets\architecture.png "Solution Design")


This repository contains two separate Python scripts for extracting text from multi-page PDF files using Optical Character Recognition (OCR). Each script utilizes a different OCR engine:

1.  **Typhoon OCR**: A cloud-based API suitable for high-quality, structured text extraction.
2.  **EasyOCR**: A local, open-source library that's ideal for both English and Thai text.

## Setup

It's recommended to set up two separate Conda environments, one for each OCR tool, to manage their dependencies.

### 1\. Typhoon OCR Setup

This setup is for the Typhoon OCR script, which uses a cloud-based API.

```bash
# Create and activate a new Conda environment for Typhoon
conda create --name typhoon-ocr-env python=3.9 -y
conda activate typhoon-ocr-env

# Install Typhoon OCR and its dependencies
pip install typhoon-ocr
sudo apt-get update && sudo apt-get install -y poppler-utils
```

### 2\. EasyOCR Setup

This setup is for the EasyOCR script, which runs locally.

```bash
# Create and activate a new Conda environment for EasyOCR
conda create --name easyocr-env python=3.9 -y
conda activate easyocr-env

# Install EasyOCR and its dependencies
sudo apt-get install -y poppler-utils -q
pip install pdf2image easyocr -q
```

-----

## 1\. Typhoon OCR Extractor (`typhoon_ocr_extractor.py`)

This script is designed for sequential multi-page PDF to TXT extraction and is enhanced for parallel execution. It handles rate limiting and API key management.

### Features

  * **Sequential Multi-Page Extraction**: Processes each page of a PDF one by one.
  * **Parallel Execution Support**: Can be run in multiple terminals/workers to process different batches of PDFs concurrently.
  * **Robust Rate Limiting**: Implements exponential backoff and jitter to handle API rate limits gracefully.
  * **Flexible API Key Management**: API keys can be provided via the command line, a Conda environment variable (`TYPHOON_OCR_API_KEY`), or a standard environment variable (`OPENAI_API_KEY`).

### Usage

```bash
# Single instance
python typhoon_ocr_extractor.py /path/to/pdfs /path/to/output your_api_key

# Single instance with named arguments
python typhoon_ocr_extractor.py --dir /path/to/pdfs --output /path/to/output --api-key your_api_key

# For parallel execution (recommended)
# You must have a different API key or worker ID for each instance to avoid conflicts.

# Terminal 1
conda activate typhoon-ocr-env
python typhoon_ocr_extractor.py ./batch1 ./output1 --worker-id 1

# Terminal 2
conda activate typhoon-ocr-env
python typhoon_ocr_extractor.py ./batch2 ./output2 --worker-id 2
```

**Note**: For parallel processing, it is highly recommended to set your API key as a Conda environment variable to keep your script clean and secure.

```bash
conda env config vars set TYPHOON_OCR_API_KEY="your_api_key"
```

-----

## 2\. EasyOCR Extractor (`easyocr_extractor.py`)

This script extracts text from PDF files using the open-source EasyOCR library, which is run locally and does not require an API key. It's optimized for both English and Thai languages.

### Features

  * **Local OCR**: No external API key is needed.
  * **Multi-Language Support**: Reads both Thai (`th`) and English (`en`) text.
  * **PDF to Image Conversion**: Uses `pdf2image` to convert each PDF page into an image for OCR processing.
  * **Page-by-Page Output**: The extracted text includes page separators (`--- Page X ---`) to maintain document structure.

### Usage

```bash
# Activate the EasyOCR environment
conda activate easyocr-env

# Run the script with input and output directories
python easyocr_extractor.py /path/to/pdfs /path/to/output
```

The script will process all `.pdf` files in the input directory and save the extracted text as `.txt` files in the output directory.