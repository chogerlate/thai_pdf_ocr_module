import os
import shutil
from pathlib import Path
import math

def get_unprocessed_files(train_docs_dir, extracted_texts_dir):
    """
    Compare PDF files in train_docs with processed .txt files in extracted_texts
    and return a list of unprocessed PDF files.
    """
    # Get all PDF files in train_docs
    train_docs_path = Path(train_docs_dir)
    pdf_files = set()
    
    if train_docs_path.exists():
        for pdf_file in train_docs_path.glob("*.pdf"):
            pdf_files.add(pdf_file.stem)  # filename without extension
    else:
        print(f"Warning: {train_docs_dir} does not exist!")
        return []
    
    # Get all processed .txt files in extracted_texts
    extracted_texts_path = Path(extracted_texts_dir)
    processed_files = set()
    
    if extracted_texts_path.exists():
        for txt_file in extracted_texts_path.glob("*.txt"):
            processed_files.add(txt_file.stem)  # filename without extension
    else:
        print(f"Warning: {extracted_texts_dir} does not exist!")
        processed_files = set()
    
    # Find unprocessed files
    unprocessed = pdf_files - processed_files
    
    return sorted(list(unprocessed))

def split_into_chunks(file_list, num_chunks=3):
    """
    Split a list of files into specified number of chunks as evenly as possible.
    """
    if not file_list:
        return [[] for _ in range(num_chunks)]
    
    chunk_size = math.ceil(len(file_list) / num_chunks)
    chunks = []
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min(start_idx + chunk_size, len(file_list))
        chunks.append(file_list[start_idx:end_idx])
    
    return chunks

def create_folders_and_copy_files(train_docs_dir, file_chunks, base_folder_name="chunk"):
    """
    Create folders for each chunk and copy the corresponding PDF files.
    """
    train_docs_path = Path(train_docs_dir)
    
    for i, chunk in enumerate(file_chunks, 1):
        if not chunk:  # Skip empty chunks
            continue
            
        # Create folder for this chunk
        folder_name = f"{base_folder_name}_{i}"
        folder_path = Path(folder_name)
        folder_path.mkdir(exist_ok=True)
        
        print(f"\nCreated folder: {folder_name}")
        print(f"Files in this chunk ({len(chunk)} files):")
        
        # Copy files to the chunk folder
        for filename in chunk:
            pdf_file = train_docs_path / f"{filename}.pdf"
            
            if pdf_file.exists():
                destination = folder_path / f"{filename}.pdf"
                shutil.copy2(pdf_file, destination)
                print(f"  ✓ Copied: {filename}.pdf")
            else:
                print(f"  ✗ Not found: {filename}.pdf")

def main():
    # Define directories
    train_docs_dir = "dataset/path_to_train_data"
    extracted_texts_dir = "extracted_texts"
    
    print("PDF File Organizer")
    print("=" * 50)
    
    # Get unprocessed files
    print("Scanning for unprocessed files...")
    unprocessed_files = get_unprocessed_files(train_docs_dir, extracted_texts_dir)
    
    if not unprocessed_files:
        print("No unprocessed files found!")
        return
    
    print(f"\nFound {len(unprocessed_files)} unprocessed files:")
    for i, filename in enumerate(unprocessed_files, 1):
        print(f"  {i:3d}. {filename}.pdf")
    
    # Split into chunks
    print(f"\nSplitting into 3 chunks...")
    chunks = split_into_chunks(unprocessed_files, 3)
    
    # Display chunk summary
    print("\nChunk distribution:")
    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i}: {len(chunk)} files")
    
    # Ask for confirmation
    response = input(f"\nProceed to create folders and copy {len(unprocessed_files)} files? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        # Create folders and copy files
        create_folders_and_copy_files(train_docs_dir, chunks)
        print(f"\n✓ Successfully organized {len(unprocessed_files)} unprocessed files into 3 chunks!")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()