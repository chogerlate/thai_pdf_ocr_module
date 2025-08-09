"""
Sequential multi-page PDF -> TXT extraction using Typhoon OCR (scb10x/typhoon-ocr-7b)
Enhanced for parallel execution with better API key management and rate limiting

Usage:
    python script.py /path/to/pdfs /path/to/output [api_key]
    python script.py --dir /path/to/pdfs --output /path/to/output --api-key your_api_key --worker-id 1
    
For parallel execution:
    # Terminal 1: conda activate worker1 && python script.py ./batch1 ./output1 --worker-id 1
    # Terminal 2: conda activate worker2 && python script.py ./batch2 ./output2 --worker-id 2
"""

from pathlib import Path
import os
import json
import time
import random
import argparse
import threading
from typing import Optional, List

try:
    from typhoon_ocr import ocr_document
except ImportError:
    raise SystemExit("typhoon-ocr not installed. Run: pip install typhoon-ocr")

# "default": markdown text, "structure": HTML tables + figure tags
TASK_TYPE = "default"

# Rate limit handling: 2 req/s, 20 req/min per API key
# With 3 different API keys, we can be more aggressive
MIN_DELAY = 0.4  # Reduced delay since we have separate API keys
MAX_RETRIES = 5

# Lock for thread-safe logging when running multiple instances
_log_lock = threading.Lock()


def safe_print(*args, **kwargs):
    """Thread-safe print function."""
    with _log_lock:
        print(*args, **kwargs)


def _parse_typhoon_response(resp) -> str:
    if isinstance(resp, str):
        try:
            parsed = json.loads(resp)
            return parsed.get("natural_text", resp)
        except json.JSONDecodeError:
            return resp
    return str(resp)


def extract_pdf_multipage(pdf_path: Path, task_type: str = TASK_TYPE, output_dir: Path = None, worker_id: str = "") -> Optional[Path]:
    """Extract all pages from PDF with rate limit handling and guaranteed file writing."""
    page_num = 1
    pages: List[str] = []
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output path in specified directory
    out_path = output_dir / f"{pdf_path.stem}.txt"

    safe_print(f"[Worker {worker_id}] Processing {pdf_path.name}...")

    while True:
        retries = 0
        page_success = False
        
        while retries < MAX_RETRIES:
            try:
                # Rate limiting: wait between requests
                if page_num > 1:
                    # Reduced jitter since each worker has its own API key
                    jitter = random.uniform(0, 0.1)
                    time.sleep(MIN_DELAY + jitter)

                resp = ocr_document(
                    pdf_or_image_path=str(pdf_path),
                    task_type=task_type,
                    page_num=page_num,
                )
                text = _parse_typhoon_response(resp).strip()
                if text:
                    pages.append(text)
                    safe_print(f"[Worker {worker_id}]   Page {page_num}: OK")
                page_success = True
                page_num += 1
                break  # Success, move to next page

            except Exception as e:
                msg = str(e).lower()
                
                # End-of-doc signals; break cleanly
                if ("page" in msg and ("not found" in msg or "invalid" in msg or "out of range" in msg)) or \
                   ("index" in msg and "range" in msg) or \
                   ("wrong page range" in msg) or \
                   ("first page" in msg and "after the last page" in msg):
                    safe_print(f"[Worker {worker_id}]   Reached end of PDF after {page_num-1} pages")
                    # Write file and return immediately
                    if pages:
                        out_path.write_text("\n\n".join(pages), encoding="utf-8")
                        safe_print(f"[Worker {worker_id}]   Wrote {len(pages)} pages to {out_path.name}")
                        return out_path
                    else:
                        safe_print(f"[Worker {worker_id}]   No text extracted from {pdf_path.name}")
                        return None
                
                # Rate limit error (429)
                if "429" in str(e) or "rate limit" in msg or "too many requests" in msg:
                    retries += 1
                    # Exponential backoff with worker-specific jitter
                    base_backoff = (2 ** retries)
                    worker_jitter = (hash(worker_id) % 10) * 0.1
                    backoff_time = base_backoff + worker_jitter + random.uniform(0, 1)
                    safe_print(f"[Worker {worker_id}]   Rate limit hit on page {page_num}. Retrying in {backoff_time:.1f}s... (attempt {retries}/{MAX_RETRIES})")
                    time.sleep(backoff_time)
                    continue
                
                # Other errors - log and continue to next page
                safe_print(f"[Worker {worker_id}]   Page {page_num}: ERROR - {e}")
                page_num += 1
                break

        # If we've exhausted retries, move to next page
        if not page_success and retries >= MAX_RETRIES:
            safe_print(f"[Worker {worker_id}]   Page {page_num}: Failed after {MAX_RETRIES} retries, skipping")
            page_num += 1

    # This should never be reached, but just in case
    if pages:
        out_path.write_text("\n\n".join(pages), encoding="utf-8")
        safe_print(f"[Worker {worker_id}]   Wrote {len(pages)} pages to {out_path.name}")
        return out_path
    else:
        safe_print(f"[Worker {worker_id}]   No text extracted from {pdf_path.name}")
        return None


def process_directory(dir_path: Path, output_dir: Path, worker_id: str = "") -> List[Path]:
    """Process all PDFs in directory sequentially."""
    if not dir_path.exists():
        safe_print(f"[Worker {worker_id}] Skip missing: {dir_path}")
        return []
    
    pdfs = sorted(dir_path.glob("*.pdf"), key=lambda p: p.name)
    if not pdfs:
        safe_print(f"[Worker {worker_id}] No PDFs in {dir_path}")
        return []

    results: List[Path] = []
    safe_print(f"[Worker {worker_id}] Processing {len(pdfs)} PDFs in {dir_path} (task_type={TASK_TYPE})")
    safe_print(f"[Worker {worker_id}] Output directory: {output_dir}")
    safe_print(f"[Worker {worker_id}] Rate limit: {MIN_DELAY}s between requests, max {MAX_RETRIES} retries per page")

    for i, pdf in enumerate(pdfs, 1):
        try:
            out = extract_pdf_multipage(pdf, TASK_TYPE, output_dir, worker_id)
            if out:
                results.append(out)
            safe_print(f"[Worker {worker_id}] [{i}/{len(pdfs)}] Completed: {pdf.name}")
        except Exception as e:
            safe_print(f"[Worker {worker_id}] [{i}/{len(pdfs)}] {pdf.name}: FATAL ERROR - {e}")
        
        # Small delay between files to be extra safe, with worker-specific jitter
        if i < len(pdfs):
            jitter = (hash(worker_id) % 10) * 0.02
            time.sleep(0.2 + jitter)

    return results


def get_api_key_priority_order(provided_key: Optional[str]) -> str:
    """Get API key with priority: provided > conda env var > regular env var."""
    # 1. Provided via command line
    if provided_key and provided_key.lower() not in ['none', 'dummy', '']:
        return provided_key
    
    # 2. Conda environment variable (set via conda env config vars set)
    conda_key = os.getenv("TYPHOON_OCR_API_KEY")
    if conda_key:
        return conda_key
    
    # 3. Regular environment variable
    regular_key = os.getenv("OPENAI_API_KEY")  # fallback
    if regular_key:
        return regular_key
    
    raise SystemExit("No API key found. Provide via: command line, conda env var (TYPHOON_OCR_API_KEY), or env var")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDFs using Typhoon OCR (parallel-ready)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Single instance
    python script.py /path/to/pdfs /path/to/output your_api_key
    
    # Parallel instances (different terminals/conda envs)
    conda activate worker1 && python script.py ./batch1 ./output1 --worker-id w1
    conda activate worker2 && python script.py ./batch2 ./output2 --worker-id w2
    
    # Using conda env vars (recommended for parallel)
    conda env config vars set TYPHOON_OCR_API_KEY=your_key
    conda activate worker1 && python script.py ./batch1 ./output1 --worker-id w1
        """
    )
    
    # Positional arguments
    parser.add_argument('dir_path', nargs='?', help='Directory containing PDF files')
    parser.add_argument('output_dir', nargs='?', help='Output directory for extracted text files')
    parser.add_argument('api_key', nargs='?', help='Typhoon OCR API key (optional if set in conda env)')
    
    # Named arguments
    parser.add_argument('-d', '--dir', dest='dir_named', help='Directory containing PDF files')
    parser.add_argument('-o', '--output', dest='output_named', help='Output directory for extracted text files')
    parser.add_argument('-k', '--api-key', dest='api_key_named', help='Typhoon OCR API key')
    parser.add_argument('-w', '--worker-id', default='main', help='Worker ID for parallel processing (default: main)')
    
    args = parser.parse_args()
    
    # Use named arguments if provided, otherwise use positional
    dir_path = args.dir_named or args.dir_path
    output_dir = args.output_named or args.output_dir
    api_key = args.api_key_named or args.api_key
    
    # Validate required arguments
    if not dir_path:
        parser.error("Directory path is required")
    if not output_dir:
        parser.error("Output directory is required")
    
    return Path(dir_path), Path(output_dir), api_key, args.worker_id


if __name__ == "__main__":
    # Parse command line arguments
    dir_path, output_dir, provided_api_key, worker_id = parse_args()
    
    # Get API key with priority order
    api_key = get_api_key_priority_order(provided_api_key)
    
    # Set the API key as environment variable
    os.environ["TYPHOON_OCR_API_KEY"] = api_key
    
    # Validate input directory
    if not dir_path.exists():
        raise SystemExit(f"Input directory does not exist: {dir_path}")
    
    if not dir_path.is_dir():
        raise SystemExit(f"Input path is not a directory: {dir_path}")
    
    safe_print(f"[Worker {worker_id}] Input directory: {dir_path}")
    safe_print(f"[Worker {worker_id}] Output directory: {output_dir}")
    safe_print(f"[Worker {worker_id}] API key: {'*' * (len(api_key) - 4)}{api_key[-4:] if len(api_key) > 4 else '****'}")
    
    # Process the directory
    results = process_directory(dir_path, output_dir, worker_id)
    
    safe_print(f"[Worker {worker_id}] Completed! Processed {len(results)} PDF files successfully.")