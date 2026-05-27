#!/usr/bin/env python3
"""Sync PDFs from files/ folder and generate vector store with proper vocab/IDF."""

import os
import json
import re
import math
from collections import defaultdict
from pathlib import Path

class VectorStore:
    def __init__(self):
        self.chunks = []
        self.vocab = {}
        self.idf = {}
    
    def _tokenize(self, text):
        tokens = re.findall(r'\b\w+\b', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'it', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
        return [t for t in tokens if t not in stop_words and len(t) > 2]
    
    def _build_vocab(self):
        """Build vocabulary from all chunks."""
        self.vocab = {}
        word_idx = 0
        for chunk in self.chunks:
            tokens = self._tokenize(chunk['text'])
            for token in tokens:
                if token not in self.vocab:
                    self.vocab[token] = word_idx
                    word_idx += 1
        print(f"  Built vocab: {len(self.vocab)} unique words")
    
    def _rebuild_idf(self):
        """Calculate IDF for all words."""
        if not self.chunks:
            self.idf = {}
            return
        self._build_vocab()
        doc_freq = defaultdict(int)
        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk['text']))
            for token in tokens:
                doc_freq[token] += 1
        num_docs = len(self.chunks)
        self.idf = {}
        for word, freq in doc_freq.items():
            self.idf[word] = math.log(num_docs / (1 + freq))
        print(f"  Built IDF for {len(self.idf)} words")
    
    def add_chunks(self, chunks):
        """Add chunks and rebuild indices."""
        self.chunks.extend(chunks)
        self._rebuild_idf()

def extract_pdf_text(pdf_path):
    """Extract text from PDF with table preservation using pdfplumber."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text += f"\n[Page {page_num}]\n"

                # Try to extract tables first
                try:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # Format table as pipe-delimited for preservation of structure
                            if table:
                                # Add header separator
                                text += "\n[TABLE]\n"
                                for row in table:
                                    # Clean row and join with pipe
                                    cells = [str(cell or "").strip() for cell in row]
                                    text += " | ".join(cells) + "\n"
                                text += "[/TABLE]\n\n"
                except Exception as e:
                    # Table extraction failed, continue with text
                    pass

                # Extract remaining text (non-table content)
                regular_text = page.extract_text() or ""
                text += regular_text

        return text
    except Exception as e:
        print(f"  ✗ Error reading {pdf_path}: {e}")
        return None

def extract_financial_metrics(text):
    """Extract key financial metrics from text/tables to preserve in chunks."""
    metrics = []

    # Look for key CRE metrics
    patterns = {
        'interest_rate': r'(?:interest rate|rate|SOFR)[:\s]+(\d+\.?\d*%|\d+\s*bps|SOFR\s*\+\s*\d+)',
        'ltc': r'(?:LTC|Loan.to.Cost)[:\s]+(\d+\.?\d*%)',
        'loan_amount': r'(?:loan amount|facility)[:\s]+\$?([\d,]+)(?:\s*M|million)?',
        'term': r'(?:term|duration)[:\s]+(\d+)\s*(?:month|year)',
        'units': r'(?:units|unit count)[:\s]+(\d+)',
        'cost_per_unit': r'(?:\$[/]?\s*unit|cost\s*per\s*unit)[:\s]+\$?([\d,]+)',
        'cost_per_sf': r'(?:\$[/]?SF|cost\s*per\s*(?:sf|square\s*foot))[:\s]+\$?([\d.]+)',
    }

    for metric_name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            metrics.append(f"[{metric_name.upper()}]: {', '.join(set(matches))}")

    return "\n".join(metrics) if metrics else ""

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def scan_and_process_pdfs(base_path):
    """Scan files folder and extract chunks."""
    vs = VectorStore()
    chunk_id = 0
    all_chunks = []

    for pdf_file in sorted(Path(base_path).rglob('*.pdf')):
        print(f"Processing: {pdf_file.name}")
        text = extract_pdf_text(str(pdf_file))
        if not text:
            continue

        # Determine document type
        rel_path = str(pdf_file.relative_to(base_path))
        if 'market_studies' in rel_path:
            doc_type = 'Market Study'
        elif 'client_projects' in rel_path:
            doc_type = 'Client Project'
        elif 'underwriting_files' in rel_path:
            doc_type = 'Underwriting File'
        elif 'deliverables' in rel_path:
            doc_type = 'Deliverable'
        else:
            doc_type = 'Document'

        # Extract client project name if applicable
        client_project = None
        if 'client_projects' in rel_path:
            parts = rel_path.split('/')
            if len(parts) > 1:
                client_project = parts[1]

        # Extract financial metrics from the entire document for indexing
        financial_metrics = extract_financial_metrics(text)

        # Chunk the text
        text_chunks = chunk_text(text)
        for idx, chunk_content in enumerate(text_chunks):
            # Extract page numbers from chunk
            page_nums = re.findall(r'\[Page (\d+)\]', chunk_content)
            page_start = int(page_nums[0]) if page_nums else 1
            page_end = int(page_nums[-1]) if page_nums else page_start

            # Prepend financial metrics to first chunk of document for better search relevance
            enriched_text = chunk_content
            if financial_metrics and idx == 0:  # Add metrics to first chunk of each document
                enriched_text = f"[KEY METRICS]\n{financial_metrics}\n\n{chunk_content}"

            chunk = {
                'text': enriched_text,
                'metadata': {
                    'file_name': pdf_file.name,
                    'file_path': str(pdf_file),
                    'doc_type': doc_type,
                    'client_project': client_project,
                    'page_start': page_start,
                    'page_end': page_end,
                    'chunk_id': chunk_id
                }
            }
            all_chunks.append(chunk)
            chunk_id += 1

        print(f"  ✓ Added {len(text_chunks)} chunks")

    # Add all chunks at once to trigger vocab/IDF rebuilding
    vs.add_chunks(all_chunks)

    return vs

def main():
    files_path = Path("/Users/bencolella/Desktop/SWG/SWAI Project/files")
    
    if not files_path.exists():
        print(f"Files path does not exist: {files_path}")
        return
    
    print(f"\n📂 Scanning {files_path}...")
    vs = scan_and_process_pdfs(files_path)
    
    print(f"\n✓ Total chunks: {len(vs.chunks)}")
    print(f"✓ Vocab size: {len(vs.vocab)}")
    print(f"✓ IDF entries: {len(vs.idf)}")
    
    # Save vector store
    output = {
        'chunks': vs.chunks,
        'vocab': vs.vocab,
        'idf': vs.idf
    }
    
    output_file = files_path.parent / "stonewater-rag-backend" / "vector_store.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Vector store saved to {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()
