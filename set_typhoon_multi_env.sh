#!/bin/bash
# Setup script for parallel PDF OCR processing with conda environments

set -e  # Exit on error

# Configuration
NUM_WORKERS=3
# Replace with your actual API keys
API_KEYS=(
    "YOUR-API-KEY"
    "YOUR-API-KEY"
    "YOUR-API-KEY"
)
BASE_ENV_NAME="ocr_worker"
PYTHON_VERSION="3.9"

echo "Setting up $NUM_WORKERS conda environments for parallel OCR processing..."

# Function to create and configure a worker environment
setup_worker() {
    local worker_num=$1
    local env_name="${BASE_ENV_NAME}${worker_num}"
    local api_key="${API_KEYS[$((worker_num-1))]}"  # Array is 0-indexed
    
    echo "Creating environment: $env_name with API key: ${api_key:0:8}..."
    
    # Create conda environment
    conda create -n "$env_name" python="$PYTHON_VERSION" -y
    
    # Activate environment and install dependencies
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$env_name"
    
    # Set environment variable for this conda environment
    conda env config vars set TYPHOON_OCR_API_KEY="$api_key"
    
    # Install required packages
    pip install typhoon-ocr
    
    echo "Environment $env_name configured successfully with unique API key"
    conda deactivate
}

# Create worker environments
for i in $(seq 1 $NUM_WORKERS); do
    setup_worker $i
done

echo "All environments created successfully!"
echo
echo "Usage examples:"
echo "# Terminal 1:"
echo "conda activate ${BASE_ENV_NAME}1"
echo "python ocr_script.py ./batch1 ./output1 --worker-id w1"
echo
echo "# Terminal 2:"
echo "conda activate ${BASE_ENV_NAME}2"
echo "python ocr_script.py ./batch2 ./output2 --worker-id w2"
echo
echo "# Terminal 3:"
echo "conda activate ${BASE_ENV_NAME}3"
echo "python ocr_script.py ./batch3 ./output3 --worker-id w3"
echo
echo "To list all environments: conda env list"
echo "To remove an environment: conda env remove -n ${BASE_ENV_NAME}1"