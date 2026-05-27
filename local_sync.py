#!/usr/bin/env python3
import sys
import os

# Change to project directory
project_path = r'/Users/bencolella/Desktop/SWG/SWAI Project'
os.chdir(project_path)
sys.path.insert(0, os.getcwd())

from document_sync import DocumentSync
from pdf_processor import PDFProcessor
from vector_store import VectorStore

# Process local PDFs
sync = DocumentSync()
new_files, removed = sync.scan_documents()
print(f"Found {len(new_files)} new/updated files")

# Process PDFs into vector store
processor = PDFProcessor()
store = VectorStore()

for file_info in new_files:
    filepath = file_info['filepath']
    metadata = file_info['metadata']
    chunks = processor.process_pdf(filepath, metadata)
    if chunks:
        store.add_chunks(chunks)
        print(f"Processed: {metadata['file_name']}")

print("Local sync complete!")
print(f"Total chunks: {store.get_stats()['total_chunks']}")
